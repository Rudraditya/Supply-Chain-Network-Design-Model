"""The Rookie Network Intelligence Lab — Streamlit Community Cloud entrypoint."""
from __future__ import annotations

import copy
import json
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from model import (PRESET_LABELS, MODULES, fixed_base_config, resize_base_config,
                   load_case, preset, solve)

st.set_page_config(
    page_title="The Rookie | Cement Network Lab",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
    /* Keep the case readable even when the viewer has selected Streamlit's dark theme. */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #f6fafb !important;
        color: #183344 !important;
    }
    [data-testid="stHeader"] {background-color: #f6fafb !important;}
    .block-container {max-width: 1460px; padding-top: 2.0rem; padding-bottom: 3rem;}
    h1, h2, h3 {color: #183344; letter-spacing: -0.025em;}
    [data-testid="stMetric"] {background: #ffffff; border: 1px solid #dce8e8;
        border-radius: 10px; padding: 16px 18px; min-height: 118px;}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
        color: #183344 !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
        color: #45606b !important;
    }
    [data-testid="stSidebar"] {background-color: #edf5f3 !important;
        border-right: 1px solid #dce8e8;}
    button[data-baseweb="tab"] {color: #183344 !important;}
    button[data-baseweb="tab"][aria-selected="true"] {color: #08736e !important;}
    .eyebrow {font-size: .78rem; font-weight: 700; letter-spacing: .14em;
        color: #08736e; margin-bottom: .4rem;}
    .intro {font-size: 1.08rem; color: #526778; max-width: 900px;}
</style>
""", unsafe_allow_html=True)

DATA = load_case()
I = [s["id"] for s in DATA["integrated_sites"]]
G = [s["id"] for s in DATA["split_sites"]]
M = [m["id"] for m in DATA["markets"]]
BASE_JSON = json.dumps(preset("Base", DATA), sort_keys=True)

@st.cache_data(show_spinner=False)
def solve_cached(config_json: str) -> dict[str, Any]:
    return solve(json.loads(config_json), DATA, time_limit=90)


def solve_config(cfg: dict) -> dict:
    return solve_cached(json.dumps(cfg, sort_keys=True))


def status_label(res: dict) -> str:
    return {"optimal": "Optimal", "incumbent": "Feasible incumbent", "infeasible": "Infeasible",
            "no_solution": "No certified solution"}.get(res["status"], res["status"])


def money(v: float | None, dec: int = 1) -> str:
    return "—" if v is None else f"₹{v:,.{dec}f} cr"


def km(v: float | None) -> str:
    return "N/A" if v is None else f"{v:,.0f} km"


def badge_rows(res: dict) -> pd.DataFrame:
    rows = []
    for s in DATA["integrated_sites"]:
        rows.append({"Facility": s["id"], "Location": s["name"], "Type": "Integrated",
                     "Module": res["integrated_modules"][s["id"]]})
    for s in DATA["split_sites"]:
        rows.append({"Facility": s["id"], "Location": s["name"], "Type": "Split grinder",
                     "Module": res["split_modules"][s["id"]]})
    return pd.DataFrame(rows)


def mode_comparison_rows(outcomes: dict[str, dict]) -> pd.DataFrame:
    rows=[]
    for label,result in outcomes.items():
        rows.append({"Decision mode":label,"Status":status_label(result),
                     "Annual cost ₹ cr":result["objective_cr"],
                     "Cement lead km":result.get("cement_lead_km"),
                     "Split grinding %":100*result["split_share"] if result["objective_cr"] is not None else None})
    return pd.DataFrame(rows)


def cost_bridge(reference: dict, redesigned: dict, reference_label: str) -> go.Figure:
    components=list(reference["cost_breakdown_cr"])
    changes=[redesigned["cost_breakdown_cr"][key]-reference["cost_breakdown_cr"][key]
             for key in components]
    fig=go.Figure(go.Waterfall(
        x=[reference_label,*components,"Redesign"],
        measure=["absolute",*["relative"]*len(components),"total"],
        y=[reference["objective_cr"],*changes,0],
        text=[f"₹{reference['objective_cr']:,.1f}",*[f"{v:+,.1f}" for v in changes],
              f"₹{redesigned['objective_cr']:,.1f}"],
        textposition="outside",
        connector={"line":{"color":"#abc4c6"}},
        increasing={"marker":{"color":"#b4644f"}},
        decreasing={"marker":{"color":"#08736e"}},
        totals={"marker":{"color":"#183b4d"}},
        hovertemplate="%{x}<br>₹%{y:,.2f} cr<extra></extra>"))
    fig.update_layout(height=440,margin=dict(l=20,r=20,t=25,b=40),
                      yaxis_title="Annual relevant cost (₹ crore)",
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      font={"family":"Arial","color":"#183344"},
                      xaxis={"tickangle":-20})
    return fig


def mode_facilities(base: dict, outcomes: dict[str, dict]) -> pd.DataFrame:
    rows=[]
    for site in I+G:
        field="integrated_modules" if site in I else "split_modules"
        rows.append({"Site":site,"Type":"Integrated" if site in I else "Split grinder",
                     "Original Base":base[field][site],
                     **{label:(result[field][site] if result["objective_cr"] is not None else "—")
                        for label,result in outcomes.items()}})
    return pd.DataFrame(rows)


def make_sankey(flows: list[dict], title: str, unit: str, color: str) -> go.Figure:
    if not flows:
        return go.Figure().update_layout(title=title)
    sources = sorted({e["source"] for e in flows})
    targets = sorted({e["target"] for e in flows})
    nodes = sources + targets
    ix = {v: i for i, v in enumerate(nodes)}
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node={"label": nodes, "pad": 16, "thickness": 13,
              "color": ["#08736e"] * len(sources) + ["#b4d8d3"] * len(targets)},
        link={"source": [ix[e["source"]] for e in flows],
              "target": [ix[e["target"]] for e in flows],
              "value": [e["mt"] for e in flows],
              "color": color,
              "customdata": [e["km"] for e in flows],
              "hovertemplate": "%{source.label} → %{target.label}<br>%{value:.3f} Mt<br>%{customdata:.0f} km<extra></extra>"}
    ))
    fig.update_layout(title=title, font={"family": "Arial", "size": 13, "color": "#183344"},
                      paper_bgcolor="rgba(0,0,0,0)", height=500, margin=dict(l=5,r=5,t=55,b=10))
    return fig


def scenario_explanation(res: dict, baseline: dict, cfg: dict) -> list[str]:
    if res["objective_cr"] is None:
        return res.get("diagnostics") or ["No feasible or certified plan was found. Try releasing a facility choice or relaxing a route limit."]
    lines = []
    delta = res["objective_cr"] - baseline["objective_cr"]
    if abs(delta) > 0.005:
        lines.append(f"The optimized annual cost changes by {money(delta, 2)} from the original Base assumptions. This compares different input conditions, not a like-for-like project saving.")
    shifts = []
    for kind, field in (("integrated", "integrated_modules"), ("split", "split_modules")):
        for site, module in res[field].items():
            old = baseline[field][site]
            if module != old:
                shifts.append(f"{site}: {old} → {module}")
    if shifts:
        lines.append("Facility changes from Base: " + "; ".join(shifts) + ".")
    else:
        lines.append("The selected facility modules match the Base design; transport flows may still change.")
    if res["clinker_lead_km"] is not None:
        lines.append(f"Cement travels {km(res['cement_lead_km'])} on average; clinker sent to split grinders travels {km(res['clinker_lead_km'])}.")
    tight = [u["site"] + " " + u["process"].lower() for u in res["site_utilization"]
             if u["utilization"] >= cfg["utilization"] - 1e-5]
    if tight:
        lines.append("At the planning utilization limit: " + ", ".join(tight[:7]) + ("…" if len(tight) > 7 else "") + ".")
    return lines


def render_solution(res: dict, baseline: dict) -> None:
    if res["objective_cr"] is None:
        st.error(f"{res['name']}: {status_label(res)}. The model cannot meet all demand under these settings.")
        for note in res.get("diagnostics", []):
            st.warning(note)
        if not res.get("diagnostics"):
            st.caption("Possible causes include a market with no legal route, insufficient regional capacity or an unavailable clinker linkage.")
        st.caption(res["message"])
        return
    if res["status"] == "incumbent":
        st.warning("A feasible solution was found, but optimality was not certified within the time limit. Review the reported gap before using it as a recommendation.")
    else:
        st.success(f"Optimal network found. MILP gap: {100 * res['gap']:.4f}% (target ≤0.01%).", icon="✅")
    delta = res["objective_cr"] - baseline["objective_cr"]
    cols = st.columns(4)
    cols[0].metric("Annual relevant cost", money(res["objective_cr"],2),
                   f"{delta:+,.2f} cr vs original Base" if abs(delta)>0.005 else "Original Base")
    cols[1].metric("Demand served", f"{res['total_demand_mt']:.2f} Mt")
    cols[2].metric("Cement from split grinding", f"{100*res['split_share']:.1f}%")
    cols[3].metric("Weighted cement lead", km(res["cement_lead_km"]))
    st.caption("Comparisons against Base change the scenario inputs. They do not represent a net saving from switching networks under identical conditions.")
    left, right = st.columns([1.05,.95], gap="large")
    with left:
        st.subheader("What the model selected")
        st.dataframe(badge_rows(res), width="stretch", hide_index=True, height=391)
    with right:
        st.subheader("Annual cost composition")
        b = res["cost_breakdown_cr"]
        fig = go.Figure(go.Pie(labels=list(b), values=list(b.values()), hole=.63,
                               marker={"colors": ["#183b4d", "#82afa1", "#0b7975", "#9dcdc8"]},
                               textinfo="percent", hovertemplate="%{label}: ₹%{value:,.1f} cr (%{percent})<extra></extra>"))
        fig.update_layout(height=345, paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                          legend={"orientation":"h","y":-0.13,"x":0},
                          margin=dict(l=5,r=5,t=10,b=55), font={"family":"Arial","color":"#183344"})
        st.plotly_chart(fig, width="stretch", key=f"cost_{res['name']}")
    st.subheader("Decision brief")
    for line in scenario_explanation(res,baseline,json.loads(st.session_state.active_json)):
        st.markdown("- " + line)
    st.caption("The model includes annualized investment, fixed operating cost, limestone and both freight legs. It omits common conversion costs by case design.")


def build_form() -> None:
    st.sidebar.markdown("### Scenario builder")
    starting = st.sidebar.selectbox("Start from a preset", list(PRESET_LABELS),
                                    format_func=lambda x: f"{x} — {PRESET_LABELS[x]}")
    p = preset(starting, DATA)
    tag = starting.split(" · ")[0]
    st.sidebar.caption("A selected preset seeds the controls below; you can change any input before optimizing.")
    with st.sidebar.form("custom_form"):
        name = st.text_input("Scenario name", value=f"Custom from {tag}", key=f"scenario_name_{tag}")
        with st.expander("Facility and grinder choices", expanded=True):
            i_df = pd.DataFrame([{ "Site": s["id"], "Location": s["name"],
                                   "Module": p["integrated_choices"][s["id"]],
                                   "Limestone ₹/t": p["limestone_rates"][s["id"]]}
                                 for s in DATA["integrated_sites"]])
            edited_i = st.data_editor(i_df, hide_index=True, width="stretch",
                disabled=["Site", "Location"], num_rows="fixed", key=f"integrated_{tag}",
                column_config={"Module": st.column_config.SelectboxColumn("Module", options=["Optimize","Open","Closed",*MODULES], required=True),
                               "Limestone ₹/t": st.column_config.NumberColumn("Limestone ₹/t",min_value=0.0,max_value=1000.0,step=5.0,required=True,
                                  help="Site-specific raw limestone cost. The source case does not specify a limestone freight lane.")})
            g_df = pd.DataFrame([{"Site": s["id"], "Location": s["name"],
                                   "Module": p["split_choices"][s["id"]]}
                                 for s in DATA["split_sites"]])
            edited_g = st.data_editor(g_df, hide_index=True, width="stretch",
                disabled=["Site", "Location"], num_rows="fixed", key=f"split_{tag}",
                column_config={"Module": st.column_config.SelectboxColumn("Module", options=["Optimize","Open","Closed",*MODULES], required=True)})
            st.caption("Optimize allows a size or closure; Open requires a site but lets the solver choose S/M/L. Selecting S/M/L fixes that module; Closed forbids it.")
            st.caption("Limestone is a site-specific input cost (₹/t), not a separate freight rate in the supplied case.")
        with st.expander("Freight, material and capital", expanded=True):
            cement_rate = st.number_input("Cement freight (₹/t-km)",0.01,20.0,float(p["cement_rate"]),0.05)
            clinker_rate = st.number_input("Clinker freight (₹/t-km)",0.01,20.0,float(p["clinker_rate"]),0.05)
            clinker_factor = st.number_input("Clinker factor (t/t cement)",0.40,1.20,float(p["clinker_factor"]),0.01,
                                             help="The case uses 0.66. A lower factor means less clinker for each tonne of cement.")
            limestone_requirement = st.number_input("Limestone (t/t clinker)",0.80,2.50,float(p["limestone_requirement"]),0.05)
            capex = st.number_input("Capex multiplier",0.50,2.00,float(p["capex_multiplier"]),0.05)
            opex = st.number_input("Fixed opex multiplier",0.50,2.00,float(p["opex_multiplier"]),0.05)
        with st.expander("Demand and lane rules"):
            util = st.slider("Maximum planned utilization",0.50,1.00,float(p["utilization"]),0.01)
            cem_limit = st.number_input("Max cement lane (km)",100,2500,int(p["cement_limit_km"]),50)
            klink_limit = st.number_input("Max clinker lane (km)",100,3000,int(p["clinker_limit_km"]),50)
            demand_df = pd.DataFrame([{"Market": m["id"], "Demand centre": m["centre"],
                                        "Target Mt": p["demand_mt"][j]}
                                       for j,m in enumerate(DATA["markets"])])
            edited_demand = st.data_editor(demand_df,hide_index=True,width="stretch",
                disabled=["Market","Demand centre"],num_rows="fixed",key=f"demand_{tag}",
                column_config={"Target Mt":st.column_config.NumberColumn("Target Mt",min_value=0.0,max_value=20.0,step=0.01,format="%.3f",required=True)})
        run = st.form_submit_button("Optimize scenario",type="primary",width="stretch")
    if run:
        cfg=copy.deepcopy(p)
        safe_name=name.strip() or "Custom"
        if safe_name in PRESET_LABELS:
            safe_name=f"Custom: {safe_name}"
        cfg.update(name=safe_name,cement_rate=cement_rate,clinker_rate=clinker_rate,
                   clinker_factor=clinker_factor,limestone_requirement=limestone_requirement,
                   capex_multiplier=capex,opex_multiplier=opex,utilization=util,
                   cement_limit_km=cem_limit,clinker_limit_km=klink_limit,
                   demand_mt=[float(v) for v in edited_demand["Target Mt"]],
                   integrated_choices={r["Site"]:r["Module"] for _,r in edited_i.iterrows()},
                   split_choices={r["Site"]:r["Module"] for _,r in edited_g.iterrows()},
                   limestone_rates={r["Site"]:float(r["Limestone ₹/t"]) for _,r in edited_i.iterrows()})
        try:
            candidate=solve_config(cfg)
        except (ValueError,AssertionError) as exc:
            st.sidebar.error(str(exc))
        else:
            st.session_state["active_json"]=json.dumps(cfg,sort_keys=True)
            st.session_state["active_result"]=candidate
            st.session_state["saved_custom"][cfg["name"]]=cfg
            st.sidebar.success(f"{cfg['name']}: {status_label(candidate)}")


if "saved_custom" not in st.session_state:
    st.session_state.saved_custom={}
if "active_json" not in st.session_state:
    st.session_state.active_json=BASE_JSON
if "active_result" not in st.session_state:
    st.session_state.active_result=solve_cached(BASE_JSON)

build_form()
baseline=solve_cached(BASE_JSON)
active=st.session_state.active_result
st.markdown('<div class="eyebrow">PRESCRIPTIVE ANALYTICS  ·  FY2030</div>',unsafe_allow_html=True)
st.title("The Rookie | Cement Network Lab")
st.markdown('<p class="intro">Choose facilities, prices, material efficiency and regional demand. The MILP reoptimizes clinker and cement flows, explains the new footprint, and tests whether the original Base modules still work.</p>',unsafe_allow_html=True)

view,modes,compare,sensitivity,network,method=st.tabs(["Executive view","Decision modes","Scenario comparison","Sensitivity lab","Network explorer","Model & interview notes"])
with view:
    st.subheader(f"Current decision: {active['name']}")
    render_solution(active,baseline)
    st.download_button("Download scenario settings (JSON)",st.session_state.active_json,
                       file_name="rookie_scenario.json",mime="application/json")
with modes:
    scenario=json.loads(st.session_state.active_json)
    st.subheader(f"Keep, resize or redesign? · {scenario['name']}")
    st.write("Each mode uses the same demand, material rates, freight rates, route rules and capacity ceiling. Only the facility choices change.")
    labels=["1 · Reroute Base modules","2 · Resize Base locations","3 · Redesign"]
    mode_results={
        labels[0]:solve_config(fixed_base_config(scenario,baseline)),
        labels[1]:solve_config(resize_base_config(scenario,baseline)),
        labels[2]:active,
    }
    st.caption("1 keeps each Base module size and reroutes flows. 2 keeps Base sites open/closed but may choose new sizes. 3 uses the scenario builder's site choices and may open or close sites. Scenario closures apply to every mode.")
    mode_table=mode_comparison_rows(mode_results)
    st.dataframe(mode_table,hide_index=True,width="stretch",
                 column_config={"Annual cost ₹ cr":st.column_config.NumberColumn(format="₹%.2f"),
                                "Cement lead km":st.column_config.NumberColumn(format="%.1f"),
                                "Split grinding %":st.column_config.NumberColumn(format="%.1f%%")})
    fixed_res,resize_res,redesign=mode_results.values()
    reference=next(((label,result) for label,result in list(mode_results.items())[:2]
                    if result["objective_cr"] is not None),None)
    if reference and redesign["objective_cr"] is not None:
        ref_label,ref=reference
        difference=ref["objective_cr"]-redesign["objective_cr"]
        if abs(difference)<.005:
            st.info(f"The redesign and {ref_label.lower()} have essentially the same annual cost under these inputs.")
        elif difference>0:
            st.success(f"Redesign reduces annual relevant cost by {money(difference,2)} versus {ref_label.lower()} under identical scenario inputs.")
        else:
            st.warning(f"Redesign costs {money(-difference,2)} more than {ref_label.lower()}. Check whether custom site/module mandates restrict the redesign.")
        st.subheader("Where the cost changes")
        st.plotly_chart(cost_bridge(ref,redesign,ref_label),width="stretch",key="mode_bridge")
        components=list(ref["cost_breakdown_cr"])
        bridge_table=pd.DataFrame([{"Cost component":key,
                                    f"{ref_label} ₹ cr":ref["cost_breakdown_cr"][key],
                                    "Redesign ₹ cr":redesign["cost_breakdown_cr"][key],
                                    "Change ₹ cr":redesign["cost_breakdown_cr"][key]-ref["cost_breakdown_cr"][key]}
                                   for key in components])
        st.dataframe(bridge_table,hide_index=True,width="stretch",
                     column_config={key:st.column_config.NumberColumn(format="₹%.2f")
                                    for key in bridge_table.columns if "₹ cr" in key})
        if resize_res["objective_cr"] is not None:
            location_value=resize_res["objective_cr"]-redesign["objective_cr"]
            if abs(location_value)<.005:
                st.info("Resizing at the original Base locations reaches the same modeled annual cost as full redesign. New sites add no cost advantage under these inputs.")
            elif location_value>0:
                st.info(f"Changing the site footprint saves another {money(location_value,2)} beyond resizing at Base locations.")
    elif redesign["objective_cr"] is not None:
        st.warning("The Base footprint cannot serve this scenario even after resizing. Redesign is feasible; there is no numeric saving against an infeasible plan.")
        newly_open=[site for site in I+G
                    if baseline["integrated_modules" if site in I else "split_modules"][site]=="Closed"
                    and redesign["integrated_modules" if site in I else "split_modules"][site]!="Closed"]
        if newly_open:
            st.info("The redesign opens " + ", ".join(newly_open) + " to restore a feasible network.")
    else:
        st.error("The chosen full redesign is infeasible under these settings. Review the site mandates, route limits and capacity.")
    for label,result in list(mode_results.items())[:2]:
        if result["objective_cr"] is None:
            for note in result.get("diagnostics",[]):
                st.caption(f"{label}: {note}")
    st.subheader("Facility decisions by mode")
    facility_table=mode_facilities(baseline,mode_results)
    st.dataframe(facility_table,hide_index=True,width="stretch")
    st.caption("A mode comparison is a like-for-like network comparison because demand, prices and route rules are held fixed. The annual cost figures include annualized capex and fixed opex; they are not a one-time cash investment appraisal.")
    st.download_button("Download decision modes (CSV)",mode_table.to_csv(index=False).encode("utf-8-sig"),
                       file_name="rookie_decision_modes.csv",mime="text/csv")
with compare:
    st.subheader("Compare alternative futures")
    selection=st.multiselect("Preset scenarios",list(PRESET_LABELS),
        default=["Base","A · Demand mix","B · Freight shock","C · I1 delay"],
        format_func=lambda k: f"{k} — {PRESET_LABELS[k]}")
    custom_names=list(st.session_state.saved_custom)
    extra=st.multiselect("Your saved custom scenarios",custom_names)
    fixed=st.checkbox("Test fixed Base modules under each scenario",value=True,
                      help="Keep Base module sizes; reoptimize legal flows. Any site made unavailable by a scenario is closed.")
    if st.button("Run comparison",type="primary"):
        rows=[];results={}
        for label in selection+extra:
            cfg=preset(label,DATA) if label in selection else st.session_state.saved_custom[label]
            outcome=solve_config(cfg)
            results[label]=outcome
            fixed_outcome=solve_config(fixed_base_config(cfg,baseline)) if fixed and outcome["objective_cr"] is not None else None
            rows.append({"Scenario":label,"Status":status_label(outcome),
                         "Annual cost ₹ cr":outcome["objective_cr"],
                         "vs Base ₹ cr":outcome["objective_cr"]-baseline["objective_cr"] if outcome["objective_cr"] is not None else None,
                         "Cement lead km":outcome.get("cement_lead_km"),
                         "Clinker lead km":outcome.get("clinker_lead_km"),
                         "Base modules feasible":("Yes" if fixed_outcome["objective_cr"] is not None else "No") if fixed_outcome else "—",
                         "Fixed-module penalty ₹ cr":(fixed_outcome["objective_cr"]-outcome["objective_cr"])
                            if fixed_outcome and fixed_outcome["objective_cr"] is not None else None})
        st.session_state.comparison_rows=rows
        st.session_state.comparison_results=results
    if st.session_state.get("comparison_rows"):
        comp=pd.DataFrame(st.session_state.comparison_rows)
        st.dataframe(comp,hide_index=True,width="stretch",
                     column_config={"Annual cost ₹ cr":st.column_config.NumberColumn(format="₹%.2f"),
                                    "vs Base ₹ cr":st.column_config.NumberColumn(format="%+.2f"),
                                    "Cement lead km":st.column_config.NumberColumn(format="%.1f"),
                                    "Clinker lead km":st.column_config.NumberColumn(format="%.1f"),
                                    "Fixed-module penalty ₹ cr":st.column_config.NumberColumn(format="%.2f")})
        feasible=comp.dropna(subset=["Annual cost ₹ cr"])
        if not feasible.empty:
            fig=go.Figure(go.Bar(y=feasible["Scenario"],x=feasible["Annual cost ₹ cr"],orientation="h",
                                 marker_color=["#08736e" if name=="Base" else "#91bcb6" for name in feasible["Scenario"]],
                                 text=[f"₹{v:,.0f}" for v in feasible["Annual cost ₹ cr"]],textposition="outside"))
            fig.update_layout(height=max(330,65*len(feasible)),margin=dict(l=10,r=65,t=20,b=45),
                              xaxis_title="Annual relevant cost (₹ crore)",yaxis={"autorange":"reversed"},
                              paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,width="stretch")
        st.caption("Fixed-module penalty compares a constrained Base-capacity solution with that scenario's own optimum under the same inputs. Infeasible fixed capacity is reported as such, not as a numeric penalty.")
        st.download_button("Download comparison (CSV)",comp.to_csv(index=False).encode("utf-8-sig"),
                           file_name="rookie_scenario_comparison.csv",mime="text/csv")
        if "C · I1 delay" in st.session_state.comparison_results:
            c=st.session_state.comparison_results["C · I1 delay"]
            if c["objective_cr"] is not None:
                st.info("I1 unavailable: the optimized design opens I2 S and changes I6 to L, G3 to L and G4 to S. Keeping the Base modules instead is infeasible because usable grinding falls below demand.")
    else:
        st.caption("Select the scenarios and run the comparison. The original Base design is used as the reference.")
with sensitivity:
    st.subheader("Find cost and footprint tipping points")
    st.write("Change one assumption at a time from the current scenario. Each point is a fresh MILP solve, so facility modules and shipments may change.")
    parameter=st.selectbox("Assumption to vary",[
        "Cement freight (₹/t-km)","Clinker freight (₹/t-km)",
        "Clinker factor (t/t cement)","I3 limestone (₹/t)",
        "Demand in all markets (%)"])
    sweep_specs={
        "Cement freight (₹/t-km)":("cement_rate",1.0,6.0),
        "Clinker freight (₹/t-km)":("clinker_rate",.5,4.0),
        "Clinker factor (t/t cement)":("clinker_factor",.50,.80),
        "I3 limestone (₹/t)":("limestone_rates",100.0,400.0),
        "Demand in all markets (%)":("demand_mt",80.0,120.0),
    }
    key,low,high=sweep_specs[parameter]
    default_val=(100.0 if key=="demand_mt" else
                 json.loads(st.session_state.active_json)[key]["I3"] if key=="limestone_rates" else
                 json.loads(st.session_state.active_json)[key])
    center=max(low,min(high,default_val))
    range_col,points_col=st.columns([3,1])
    with range_col:
        lower,upper=st.slider("Range",min_value=low,max_value=high,
                              value=(max(low,round(center*.8,2)),min(high,round(center*1.2,2))))
    with points_col:
        points=st.select_slider("Number of solves",options=[5,7,9],value=7)
    if st.button("Run sensitivity",type="primary"):
        cfg_origin=json.loads(st.session_state.active_json)
        rows=[]
        for val in [lower+(upper-lower)*i/(points-1) for i in range(points)]:
            config=copy.deepcopy(cfg_origin)
            if key=="limestone_rates":
                config[key]["I3"]=val
            elif key=="demand_mt":
                config[key]=[v*val/100 for v in cfg_origin[key]]
            else:
                config[key]=val
            config["name"]=f"Sensitivity: {parameter} = {val:.3f}"
            result=solve_config(config)
            modules=", ".join(f"{site} {mod}" for site,mod in
                              (result.get("integrated_modules",{}) | result.get("split_modules",{})).items()
                              if mod!="Closed")
            rows.append({"Input":round(val,3),"Cost ₹ cr":result["objective_cr"],
                         "Status":status_label(result),"Open modules":modules})
        st.session_state.sweep={"parameter":parameter,"source":cfg_origin["name"],"rows":rows}
    sweep=st.session_state.get("sweep")
    if sweep:
        st.caption(f"Results for {sweep['source']} · {sweep['parameter']}")
        frame=pd.DataFrame(sweep["rows"])
        viable=frame.dropna(subset=["Cost ₹ cr"])
        if not viable.empty:
            fig=go.Figure(go.Scatter(x=viable["Input"],y=viable["Cost ₹ cr"],mode="lines+markers",
                                     line={"color":"#08736e","width":3},marker={"size":10},
                                     hovertemplate="Input: %{x:.3f}<br>Cost: ₹%{y:,.2f} cr<extra></extra>"))
            fig.update_layout(xaxis_title=sweep["parameter"],yaxis_title="Optimized annual cost (₹ crore)",
                              height=370,margin=dict(l=20,r=20,t=15,b=25),
                              paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,width="stretch")
        st.dataframe(frame,hide_index=True,width="stretch",
                     column_config={"Cost ₹ cr":st.column_config.NumberColumn(format="₹%.2f")})
        st.caption("Changes in the input alter the economic environment. Review the module column for discrete investment switches; infeasible points have no cost.")
        st.download_button("Download sensitivity (CSV)",frame.to_csv(index=False).encode("utf-8-sig"),
                           file_name="rookie_sensitivity.csv",mime="text/csv")
with network:
    st.subheader(f"Network explorer: {active['name']}")
    if active["objective_cr"] is None:
        st.warning("There is no network to inspect for an infeasible scenario.")
    else:
        k1,k2,k3=st.columns(3)
        k1.metric("Integrated sites open",sum(v!="Closed" for v in active["integrated_modules"].values()))
        k2.metric("Split grinders open",sum(v!="Closed" for v in active["split_modules"].values()))
        k3.metric("Max selected-site utilization",f"{100*active['max_utilization']:.1f}%")
        cm,ck,util=st.tabs(["Cement routes","Clinker routes","Capacity use"])
        with cm:
            flows=active["integrated_cement_flows"]+active["split_cement_flows"]
            st.plotly_chart(make_sankey(flows,"Finished cement: production site to market (Mt)","Mt","rgba(8,115,110,.27)"),width="stretch")
            st.dataframe(pd.DataFrame(flows).sort_values("mt",ascending=False).rename(columns={"source":"From","target":"Market","mt":"Mt","km":"km"}),
                         hide_index=True,width="stretch")
            st.download_button("Download cement routes (CSV)",pd.DataFrame(flows).to_csv(index=False).encode("utf-8-sig"),
                               "cement_routes.csv","text/csv")
        with ck:
            flows=active["clinker_flows"]
            if flows:
                st.plotly_chart(make_sankey(flows,"Clinker: integrated plant to split grinder (Mt)","Mt","rgba(24,59,77,.29)"),width="stretch")
                st.dataframe(pd.DataFrame(flows).sort_values("mt",ascending=False).rename(columns={"source":"From","target":"Grinder","mt":"Mt","km":"km"}),
                             hide_index=True,width="stretch")
                st.download_button("Download clinker routes (CSV)",pd.DataFrame(flows).to_csv(index=False).encode("utf-8-sig"),
                                   "clinker_routes.csv","text/csv")
            else:
                st.info("This network uses no split-grinding clinker shipments.")
        with util:
            usage=pd.DataFrame(active["site_utilization"])
            usage["Utilization %"]=(100*usage["utilization"]).round(1)
            st.dataframe(usage[["site","process","module","used_mt","nameplate_mtpa","Utilization %"]],
                         hide_index=True,width="stretch")
            st.caption("Clinker and integrated grinding are checked separately; the planning ceiling comes from the chosen scenario.")
with method:
    st.subheader("What the app solves")
    st.write("A mixed-integer linear program chooses one module or closure at each site, then routes clinker and finished cement to meet all market demand at the lowest annual relevant cost.")
    st.markdown("**Decision variables:** binary site/module choices; nonnegative clinker flows (I → G), direct cement flows (I → M) and split cement flows (G → M).")
    st.markdown("**Objective:** annualized capex + fixed opex + site-specific limestone + finished-cement freight + clinker freight.")
    st.markdown("**Constraints:** every market is served; 0.66 t clinker per tonne of cement by default; clinker and grinding stay within 90% of selected nameplate; one module at most per site (exactly one when Open is required); normal route caps are 800 km cement and 1,300 km clinker.")
    st.info("The app is prescriptive optimization, not a machine-learning forecast. Its explanations are computed from exact model outputs and do not call a language model.")
    with st.expander("Model checks and interpretation"):
        st.write("Each solve reconciles the objective to its four cost components, checks all 12 market balances and validates selected-site capacity. The solver seeks an integer optimality gap of 0.01% or less. A time-limited incumbent is clearly labeled.")
        st.write("The case omits common conversion costs, taxes, working capital, implementation timing and uncertainty probabilities. Its market locations and distances are planning centroids rather than live logistics routes. Scenario differences are comparisons under changed inputs, not causal savings from a facility switch.")
    with st.expander("How to describe this project in an interview"):
        st.write("I translated a manufacturing network case into a MILP, exposed key assumptions in a web app, and validated the optimized Base and required scenarios against the Excel model. Users can test rerouting, resizing and full redesign under identical conditions, then stress-test closures, freight, material intensity, capacity and regional demand.")
        st.write("The decision insight: the Base network is lowest cost under stated assumptions, but an I1 project delay makes its fixed installed capacity infeasible. The app identifies a reoptimized fallback instead of treating a single optimum as robust by default.")
    st.caption("Source: The Rookie FY2030 teaching-case workbook supplied for this assignment. No external market data is used.")
