"""Auditable MILP engine for The Rookie cement network teaching case.

Costs are annual ₹ crore; flows are Mt/year. SciPy's HiGHS-backed MILP is used
with a 0.01% relative gap target, matching the assignment's Solver requirement.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

DATA_PATH = Path(__file__).parent / "data" / "case_data.json"
MODULES = ("S", "M", "L")
PRESET_LABELS = {
    "Base": "Original FY2030 plan",
    "A · Demand mix": "Required A: regional demand shift",
    "B · Freight shock": "Required B: cement and clinker freight rise",
    "C · I1 delay": "Required C: Chittorgarh (I1) unavailable",
    "D · I3 limestone": "Optional: I3 limestone ₹195 → ₹300/t",
    "E · G1 closure": "Management stress test: Dadri grinder unavailable",
    "F · 600 km cement": "Management stress test: tighter cement-lane policy",
    "G · 10% demand": "Growth stress test: all markets +10%",
}


def load_case() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def base_config(data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or load_case()
    d = data["defaults"]
    return {
        "name": "Base",
        "demand_mt": [m["base_demand_mt"] for m in data["markets"]],
        "cement_rate": d["cement_freight_inr_per_tkm"],
        "clinker_rate": d["clinker_freight_inr_per_tkm"],
        "limestone_rates": {s["id"]: s["limestone_inr_per_t"] for s in data["integrated_sites"]},
        "clinker_factor": d["clinker_factor"],
        "limestone_requirement": d["limestone_t_per_t_clinker"],
        "utilization": d["max_utilization"],
        "cement_limit_km": d["cement_lane_max_km"],
        "clinker_limit_km": d["clinker_lane_max_km"],
        "capex_multiplier": 1.0,
        "opex_multiplier": 1.0,
        "integrated_choices": {s["id"]: "Optimize" for s in data["integrated_sites"]},
        "split_choices": {s["id"]: "Optimize" for s in data["split_sites"]},
    }


def preset(name: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or load_case()
    if name not in PRESET_LABELS:
        raise ValueError(f"Unknown preset: {name}")
    cfg = base_config(data)
    cfg["name"] = name
    if name == "A · Demand mix":
        cfg["demand_mt"] = [m["scenario_a_demand_mt"] for m in data["markets"]]
    elif name == "B · Freight shock":
        cfg["cement_rate"] = 3.75
        cfg["clinker_rate"] = 1.85
    elif name == "C · I1 delay":
        cfg["integrated_choices"]["I1"] = "Closed"
    elif name == "D · I3 limestone":
        cfg["limestone_rates"]["I3"] = 300.0
    elif name == "E · G1 closure":
        cfg["split_choices"]["G1"] = "Closed"
    elif name == "F · 600 km cement":
        cfg["cement_limit_km"] = 600
    elif name == "G · 10% demand":
        cfg["demand_mt"] = [round(v * 1.10, 6) for v in cfg["demand_mt"]]
    return cfg


def fixed_base_config(scenario: dict[str, Any], base_result: dict[str, Any]) -> dict[str, Any]:
    """Use Base modules, except that a scenario's unavailable site stays closed."""
    c = copy.deepcopy(scenario)
    for site, module in base_result["integrated_modules"].items():
        if c["integrated_choices"].get(site) != "Closed":
            c["integrated_choices"][site] = module
    for site, module in base_result["split_modules"].items():
        if c["split_choices"].get(site) != "Closed":
            c["split_choices"][site] = module
    c["name"] = scenario["name"] + " · fixed Base modules"
    return c


def validate_config(cfg: dict[str, Any], data: dict[str, Any]) -> None:
    if len(cfg["demand_mt"]) != 12 or any(not np.isfinite(v) or v < 0 for v in cfg["demand_mt"]):
        raise ValueError("Enter 12 nonnegative market demands.")
    for key in ("cement_rate", "clinker_rate", "clinker_factor", "limestone_requirement", "utilization",
                "cement_limit_km", "clinker_limit_km", "capex_multiplier", "opex_multiplier"):
        if not np.isfinite(cfg[key]) or cfg[key] <= 0:
            raise ValueError(f"{key} must be positive.")
    if cfg["utilization"] > 1:
        raise ValueError("Maximum utilization cannot exceed 100%.")
    for site in data["integrated_sites"]:
        sid = site["id"]
        if cfg["integrated_choices"].get(sid) not in ("Optimize", "Closed", *MODULES):
            raise ValueError(f"Invalid module choice for {sid}.")
        if not np.isfinite(cfg["limestone_rates"][sid]) or cfg["limestone_rates"][sid] < 0:
            raise ValueError(f"Limestone rate for {sid} must be nonnegative.")
    for site in data["split_sites"]:
        if cfg["split_choices"].get(site["id"]) not in ("Optimize", "Closed", *MODULES):
            raise ValueError(f"Invalid module choice for {site['id']}.")


def _capacity_diagnostic(cfg: dict[str, Any], data: dict[str, Any]) -> list[str]:
    def best(site_id: str, choices: dict[str, str], modules: list[dict], field: str) -> float:
        choice = choices[site_id]
        if choice == "Closed":
            return 0
        if choice == "Optimize":
            return max(m[field] for m in modules)
        return next(m[field] for m in modules if m["id"] == choice)

    grind = sum(best(s["id"], cfg["integrated_choices"], data["integrated_modules"], "grinding_mtpa")
                for s in data["integrated_sites"])
    grind += sum(best(s["id"], cfg["split_choices"], data["split_modules"], "grinding_mtpa")
                 for s in data["split_sites"])
    clinker = sum(best(s["id"], cfg["integrated_choices"], data["integrated_modules"], "clinker_mtpa")
                  for s in data["integrated_sites"])
    required = sum(cfg["demand_mt"])
    notes = []
    if grind * cfg["utilization"] + 1e-7 < required:
        notes.append(f"Maximum usable grinding is {grind * cfg['utilization']:.2f} Mt, below demand of {required:.2f} Mt.")
    if clinker * cfg["utilization"] + 1e-7 < cfg["clinker_factor"] * required:
        notes.append(f"Maximum usable clinker is {clinker * cfg['utilization']:.2f} Mt, below the required {cfg['clinker_factor'] * required:.2f} Mt.")
    return notes


def solve(cfg: dict[str, Any], data: dict[str, Any] | None = None,
          time_limit: float = 60.0) -> dict[str, Any]:
    data = data or load_case()
    validate_config(cfg, data)
    ids_i = [s["id"] for s in data["integrated_sites"]]
    ids_g = [s["id"] for s in data["split_sites"]]
    ids_m = [m["id"] for m in data["markets"]]
    d_i_m = np.array(data["distances_km"]["integrated_to_market"])
    d_g_m = np.array(data["distances_km"]["split_to_market"])
    d_i_g = np.array(data["distances_km"]["integrated_to_split"])
    alpha = float(cfg["clinker_factor"])
    beta = float(cfg["limestone_requirement"])
    util = float(cfg["utilization"])
    rate_c = float(cfg["cement_rate"])
    rate_k = float(cfg["clinker_rate"])
    r = data["defaults"]["hurdle_rate"]
    n = data["defaults"]["asset_life_years"]
    crf = r * (1 + r) ** n / ((1 + r) ** n - 1)

    yi = {(i, k): 3 * i + k for i in range(6) for k in range(3)}
    yg = {(g, k): 18 + 3 * g + k for g in range(4) for k in range(3)}
    index = 30
    xi, xg, z = {}, {}, {}
    for i in range(6):
        for m in range(12):
            if d_i_m[i, m] <= cfg["cement_limit_km"]:
                xi[i, m] = index
                index += 1
    for g in range(4):
        for m in range(12):
            if d_g_m[g, m] <= cfg["cement_limit_km"]:
                xg[g, m] = index
                index += 1
    for i in range(6):
        for g in range(4):
            if d_i_g[i, g] <= cfg["clinker_limit_km"]:
                z[i, g] = index
                index += 1

    objective = np.zeros(index)
    lb = np.zeros(index)
    ub = np.full(index, np.inf)
    ub[:30] = 1
    for (i, k), j in yi.items():
        module = data["integrated_modules"][k]
        objective[j] = (crf * module["capex_cr"] * cfg["capex_multiplier"]
                        + module["fixed_opex_cr_yr"] * cfg["opex_multiplier"])
    for (g, k), j in yg.items():
        module = data["split_modules"][k]
        objective[j] = (crf * module["capex_cr"] * cfg["capex_multiplier"]
                        + module["fixed_opex_cr_yr"] * cfg["opex_multiplier"])

    for i, sid in enumerate(ids_i):
        choice = cfg["integrated_choices"][sid]
        for k in range(3):
            j = yi[i, k]
            if choice == "Closed" or (choice in MODULES and MODULES[k] != choice):
                ub[j] = 0
            elif choice == MODULES[k]:
                lb[j] = 1
        lime = cfg["limestone_rates"][sid]
        for m in range(12):
            if (i, m) in xi:
                objective[xi[i, m]] = 0.1 * (rate_c * d_i_m[i, m] + beta * lime * alpha)
        for g in range(4):
            if (i, g) in z:
                objective[z[i, g]] = 0.1 * (rate_k * d_i_g[i, g] + beta * lime)
    for g, sid in enumerate(ids_g):
        choice = cfg["split_choices"][sid]
        for k in range(3):
            j = yg[g, k]
            if choice == "Closed" or (choice in MODULES and MODULES[k] != choice):
                ub[j] = 0
            elif choice == MODULES[k]:
                lb[j] = 1
        for m in range(12):
            if (g, m) in xg:
                objective[xg[g, m]] = 0.1 * rate_c * d_g_m[g, m]

    entries, lo, hi = [], [], []
    def add(row: dict[int, float], low: float = -np.inf, high: float = np.inf) -> None:
        entries.append(row)
        lo.append(low)
        hi.append(high)

    for i in range(6):
        add({yi[i, k]: 1 for k in range(3)}, high=1)
    for g in range(4):
        add({yg[g, k]: 1 for k in range(3)}, high=1)
    for m in range(12):
        row = {j: 1 for (i, mm), j in xi.items() if mm == m}
        row.update({j: 1 for (g, mm), j in xg.items() if mm == m})
        add(row, low=cfg["demand_mt"][m], high=cfg["demand_mt"][m])
    for i in range(6):
        row = {j: 1 for (ii, m), j in xi.items() if ii == i}
        row.update({yi[i, k]: -util * data["integrated_modules"][k]["grinding_mtpa"] for k in range(3)})
        add(row, high=0)
        row = {j: alpha for (ii, m), j in xi.items() if ii == i}
        row.update({j: 1 for (ii, g), j in z.items() if ii == i})
        row.update({yi[i, k]: -util * data["integrated_modules"][k]["clinker_mtpa"] for k in range(3)})
        add(row, high=0)
    for g in range(4):
        row = {j: 1 for (i, gg), j in z.items() if gg == g}
        row.update({j: -alpha for (gg, m), j in xg.items() if gg == g})
        add(row, low=0, high=0)
        row = {j: 1 for (gg, m), j in xg.items() if gg == g}
        row.update({yg[g, k]: -util * data["split_modules"][k]["grinding_mtpa"] for k in range(3)})
        add(row, high=0)

    rr, cc, vv = [], [], []
    for rowno, row in enumerate(entries):
        for col, coeff in row.items():
            rr.append(rowno); cc.append(col); vv.append(coeff)
    matrix = coo_matrix((vv, (rr, cc)), shape=(len(entries), index)).tocsr()
    res = milp(objective, integrality=np.r_[np.ones(30, dtype=int), np.zeros(index-30, dtype=int)],
               bounds=Bounds(lb, ub), constraints=LinearConstraint(matrix, lo, hi),
               options={"mip_rel_gap": 0.0001, "time_limit": float(time_limit)})
    if res.x is None:
        return {"name": cfg["name"], "status": "infeasible" if res.status == 2 else "no_solution",
                "message": str(res.message), "diagnostics": _capacity_diagnostic(cfg, data),
                "objective_cr": None, "gap": None}
    x = np.maximum(np.asarray(res.x), 0)
    def flows(mapping: dict[tuple[int, int], int], sources: list[str], targets: list[str], distances: np.ndarray) -> list[dict]:
        return [{"source": sources[a], "target": targets[b], "mt": float(x[j]), "km": float(distances[a, b])}
                for (a, b), j in mapping.items() if x[j] > 1e-6]
    cement_i = flows(xi, ids_i, ids_m, d_i_m)
    cement_g = flows(xg, ids_g, ids_m, d_g_m)
    clinker = flows(z, ids_i, ids_g, d_i_g)
    chosen_i = {sid: next((MODULES[k] for k in range(3) if x[yi[i, k]] > 0.5), "Closed")
                for i, sid in enumerate(ids_i)}
    chosen_g = {sid: next((MODULES[k] for k in range(3) if x[yg[g, k]] > 0.5), "Closed")
                for g, sid in enumerate(ids_g)}
    fixed = sum(objective[yi[i, k]] * round(x[yi[i, k]]) for i in range(6) for k in range(3))
    fixed += sum(objective[yg[g, k]] * round(x[yg[g, k]]) for g in range(4) for k in range(3))
    cement_freight = .1 * rate_c * sum(e["mt"] * e["km"] for e in cement_i+cement_g)
    clinker_freight = .1 * rate_k * sum(e["mt"] * e["km"] for e in clinker)
    limestone = 0.0
    site_util = []
    for i, sid in enumerate(ids_i):
        direct = sum(e["mt"] for e in cement_i if e["source"] == sid)
        shipped = sum(e["mt"] for e in clinker if e["source"] == sid)
        used = alpha * direct + shipped
        limestone += .1 * beta * cfg["limestone_rates"][sid] * used
        module = chosen_i[sid]
        if module != "Closed":
            mod = next(m for m in data["integrated_modules"] if m["id"] == module)
            site_util += [{"site": sid, "process": "Clinker", "module": module, "used_mt": used,
                           "nameplate_mtpa": mod["clinker_mtpa"], "utilization": used/mod["clinker_mtpa"]},
                          {"site": sid, "process": "Grinding", "module": module, "used_mt": direct,
                           "nameplate_mtpa": mod["grinding_mtpa"], "utilization": direct/mod["grinding_mtpa"]}]
    for g, sid in enumerate(ids_g):
        output = sum(e["mt"] for e in cement_g if e["source"] == sid)
        module = chosen_g[sid]
        if module != "Closed":
            mod = next(m for m in data["split_modules"] if m["id"] == module)
            site_util.append({"site": sid, "process": "Grinding", "module": module, "used_mt": output,
                              "nameplate_mtpa": mod["grinding_mtpa"], "utilization": output/mod["grinding_mtpa"]})
    breakdown = {"Annualized capex + fixed opex": float(fixed), "Limestone": float(limestone),
                 "Cement freight": float(cement_freight), "Clinker freight": float(clinker_freight)}
    total = sum(breakdown.values())
    if abs(total - float(res.fun)) > 1e-4:
        raise AssertionError(f"Cost reconciliation failed: {total} vs {res.fun}")
    delivered = {mid: sum(e["mt"] for e in cement_i+cement_g if e["target"] == mid) for mid in ids_m}
    if max(abs(delivered[mid] - cfg["demand_mt"][m]) for m, mid in enumerate(ids_m)) > 1e-5:
        raise AssertionError("Market balance failed")
    if any(u["utilization"] > util+1e-5 for u in site_util):
        raise AssertionError("Capacity validation failed")
    clinker_mt = sum(e["mt"] for e in clinker)
    cement_mt = sum(e["mt"] for e in cement_i+cement_g)
    result = {
        "name": cfg["name"], "status": "optimal" if res.status == 0 else "incumbent",
        "message": str(res.message), "gap": float(res.mip_gap) if res.mip_gap is not None else None,
        "objective_cr": total, "cost_breakdown_cr": breakdown,
        "total_demand_mt": float(sum(cfg["demand_mt"])),
        "integrated_modules": chosen_i, "split_modules": chosen_g,
        "integrated_cement_flows": cement_i, "split_cement_flows": cement_g,
        "clinker_flows": clinker, "market_served_mt": delivered,
        "site_utilization": site_util,
        "cement_lead_km": sum(e["mt"]*e["km"] for e in cement_i+cement_g)/cement_mt if cement_mt else None,
        "clinker_lead_km": sum(e["mt"]*e["km"] for e in clinker)/clinker_mt if clinker_mt else None,
        "split_share": sum(e["mt"] for e in cement_g)/cement_mt if cement_mt else 0,
        "max_utilization": max((u["utilization"] for u in site_util), default=0),
        "installed_clinker_mtpa": sum(data["integrated_modules"][MODULES.index(v)]["clinker_mtpa"]
                                        for v in chosen_i.values() if v != "Closed"),
        "installed_grinding_mtpa": sum(data["integrated_modules"][MODULES.index(v)]["grinding_mtpa"]
                                         for v in chosen_i.values() if v != "Closed")
        + sum(data["split_modules"][MODULES.index(v)]["grinding_mtpa"]
              for v in chosen_g.values() if v != "Closed"),
        "diagnostics": [],
    }
    return result
