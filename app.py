"""The Rookie Network Intelligence Lab — Streamlit Community Cloud entrypoint."""
from __future__ import annotations

import copy
import html
import json
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from model import (PRESET_LABELS, MODULES, fixed_base_config, resize_base_config,
                   load_case, preset, solve, validate_config)

st.set_page_config(
    page_title="The Rookie | Cement Network Lab",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown("""
<style>
    :root, [data-testid="stApp"] {
        color-scheme: light !important;
        --primary-color: #08736e !important;
        --background-color: #f6fafb !important;
        --secondary-background-color: #edf5f3 !important;
        --text-color: #183344 !important;
    }
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
    [data-testid="stSidebar"] {background-color: #183344 !important;
        color: #f6fafb !important; border-right: 1px solid #315767;}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] > div > div > div > p {
        color: #f6fafb !important;
    }
    [data-testid="stMain"] [role="tab"], [data-testid="stMain"] [role="tab"] * {
        color: #355260 !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline-color: #08736e !important;
    }
    [data-testid="stMain"] [role="tab"][aria-selected="true"],
    [data-testid="stMain"] [role="tab"][aria-selected="true"] * {
        color: #08736e !important; font-weight: 700 !important;
        border-bottom-color: #08736e !important;
        border-left-color: transparent !important; border-right-color: transparent !important;
    }
    [data-testid="stMain"] [role="tab"][aria-selected="true"]::after,
    [data-testid="stMain"] [role="tab"][aria-selected="true"]::before {
        background-color: #08736e !important; border-color: #08736e !important;
    }
    [data-testid="stMain"] [role="tab"]:focus-visible {
        outline: 2px solid #08736e !important; outline-offset: 2px !important;
    }
    [data-testid="stMain"] [role="tab"]:hover,
    [data-testid="stMain"] [role="tab"]:hover * {
        color: #08736e !important; background-color: #e8f3f1 !important;
    }
    [data-testid="stMain"] [data-baseweb="tab-highlight"] {
        background-color: #08736e !important;
    }
    [data-testid="stMain"] [data-testid="stBaseButton-secondary"],
    [data-testid="stMain"] [data-testid="stDownloadButton"] button,
    [data-testid="stMain"] button[kind="secondary"] {
        background-color: #ffffff !important; color: #183344 !important;
        border: 1px solid #9ab8b6 !important; box-shadow: none !important;
    }
    [data-testid="stMain"] [data-testid="stBaseButton-secondary"] *,
    [data-testid="stMain"] [data-testid="stDownloadButton"] button * {
        color: #183344 !important;
    }
    [data-testid="stBaseButton-primary"],
    [data-testid="stMain"] button[kind="primary"] {
        background-color: #08736e !important; color: #ffffff !important;
        border: 1px solid #08736e !important; box-shadow: none !important;
    }
    [data-testid="stBaseButton-primary"] *,
    [data-testid="stMain"] button[kind="primary"] * {color: #ffffff !important;}
    [data-testid="stMain"] [data-baseweb="select"],
    [data-testid="stMain"] [data-baseweb="select"] div,
    [data-testid="stMain"] [data-baseweb="input"],
    [data-testid="stMain"] [data-baseweb="input"] div,
    [data-testid="stMain"] [data-baseweb="base-input"],
    [data-testid="stMain"] [data-baseweb="textarea"] {
        background: #ffffff !important; color: #183344 !important;
        border-color: #9ab8b6 !important; color-scheme: light !important;
    }
    [data-testid="stMain"] [data-testid="stSelectbox"] div,
    [data-testid="stMain"] [data-testid="stMultiSelect"] div,
    [data-testid="stMain"] [data-testid="stTextInput"] div,
    [data-testid="stMain"] [data-testid="stNumberInput"] div {
        background-color: #ffffff !important; color: #183344 !important;
        border-color: #9ab8b6 !important;
    }
    [data-testid="stMain"] [data-baseweb="select"]:focus-within,
    [data-testid="stMain"] [data-baseweb="input"]:focus-within {
        border-color: #08736e !important; box-shadow: 0 0 0 1px #08736e !important;
    }
    [data-testid="stMain"] input,
    [data-testid="stMain"] textarea,
    [data-testid="stMain"] [data-baseweb="select"] > div * {
        color: #183344 !important;
    }
    [data-testid="stMain"] [data-baseweb="tag"],
    [data-testid="stMain"] [data-baseweb="tag"] * {
        background-color: #08736e !important; color: #ffffff !important;
        fill: #ffffff !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"],
    [data-baseweb="popover"] *, [data-baseweb="menu"] * {
        background-color: #ffffff !important; color: #183344 !important;
    }
    [data-testid="stMain"] input[type="checkbox"] {accent-color: #08736e !important;}
    [data-testid="stMain"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] * {
        border-color: #08736e !important;
    }
    [data-testid="stMain"] [data-testid="stWidgetLabel"] *,
    [data-testid="stMain"] [data-testid="stCaptionContainer"] * {
        color: #45606b !important;
    }
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
        color: #355260 !important;
    }
    [data-testid="stMain"] [data-testid="stAlert"] *,
    [data-testid="stMain"] [data-testid="stMetricDelta"] * {
        color: #183344 !important;
    }
    [data-testid="stMain"] [data-testid="stNumberInput"] button {
        background: #dcefeb !important; color: #183344 !important;
        border: 1px solid #9ab8b6 !important; opacity: 1 !important;
        visibility: visible !important; box-shadow: none !important;
    }
    [data-testid="stMain"] [data-testid="stNumberInput"] button svg,
    [data-testid="stMain"] [data-testid="stNumberInput"] button svg * {
        color: #183344 !important; fill: #183344 !important;
        stroke: #183344 !important; opacity: 1 !important;
    }
    [data-testid="stMain"] [data-testid="stNumberInput"] button:hover {
        background: #08736e !important; color: #ffffff !important;
    }
    [data-testid="stMain"] [data-testid="stNumberInput"] button:hover svg,
    [data-testid="stMain"] [data-testid="stNumberInput"] button:hover svg * {
        color: #ffffff !important; fill: #ffffff !important; stroke: #ffffff !important;
    }
    [data-testid="stMain"] [data-baseweb="select"] svg,
    [data-testid="stMain"] [data-baseweb="select"] svg *,
    [data-baseweb="menu"] svg {
        color: #183344 !important; fill: #183344 !important;
        stroke: #183344 !important; opacity: 1 !important;
    }
    [data-testid="stMain"] [data-testid="stToggle"] [aria-checked="true"],
    [data-testid="stMain"] [data-testid="stToggle"] input:checked + div,
    [data-testid="stMain"] [data-testid="stToggle"] [role="switch"][aria-checked="true"] {
        background-color: #08736e !important;
    }
    [data-testid="stMain"] [data-testid="stSlider"] [role="slider"] {
        background: #08736e !important; border-color: #08736e !important;
    }
    .case-table {border-collapse: collapse; width: 100%; background: #fff;
        color: #183344; margin: .5rem 0 1rem; font-size: .92rem;}
    .case-table th {text-align: left; background: #eaf3f1; color: #183344;
        font-weight: 700; padding: .65rem .8rem; border-bottom: 1px solid #c9dcda;}
    .case-table td {padding: .55rem .8rem; border-bottom: 1px solid #e0ebea;}
    .case-table td.changed {background: #fff0f1; color: #a12632 !important;
        font-weight: 750; border-left: 3px solid #c63745;}
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


def light_table(rows: list[dict], baseline_rows: list[dict] | None = None) -> None:
    """Light HTML table, optionally marking changed values against aligned baseline rows."""
    if not rows:
        return
    columns=list(rows[0])
    output=['<table class="case-table"><thead><tr>']
    output.extend(f'<th>{html.escape(str(col))}</th>' for col in columns)
    output.append('</tr></thead><tbody>')
    for j,row in enumerate(rows):
        output.append('<tr>')
        for col in columns:
            value=row.get(col,"")
            reference=baseline_rows[j].get(col,"") if baseline_rows else value
            if isinstance(value,(int,float)) and isinstance(reference,(int,float)):
                changed=abs(float(value)-float(reference))>1e-7
            else:
                changed=value!=reference
            content="—" if value is None else html.escape(str(value))
            output.append(f'<td class="{"changed" if changed else ""}">{content}</td>')
        output.append('</tr>')
    output.append('</tbody></table>')
    st.markdown(''.join(output),unsafe_allow_html=True)


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
        lines.append(f"At the {100*cfg['utilization']:.0f}% planning utilization limit: "
                     + ", ".join(tight) + ".")
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
        st.plotly_chart(fig, width="stretch", key=f"cost_{res['name']}", theme=None)
    st.subheader("Decision brief")
    for line in scenario_explanation(res,baseline,json.loads(st.session_state.active_json)):
        st.markdown("- " + line)
    st.caption("The model includes annualized investment, fixed operating cost, limestone and both freight legs. It omits common conversion costs by case design.")


def render_decision_studio() -> None:
    st.subheader("Decision studio")
    st.write("1. Set any inputs across the sections. 2. Lock the completed decisions. 3. Optimize the locked scenario and save it under a name for comparison.")
    starting = st.selectbox("Start from a preset", list(PRESET_LABELS),
                            format_func=lambda x: f"{x} — {PRESET_LABELS[x]}", key="studio_preset")
    p = preset(starting, DATA)
    tag = list(PRESET_LABELS).index(starting)
    st.caption("Freight rates and cost multipliers are in Freight & costs. A switch turned off forces a site closed. Percent changes apply to the selected preset. Finish in Review & run.")
    facilities, markets, capacities, economics, rules, review = st.tabs(
        ["Sites on/off", "Market demand", "Rated capacity", "Freight & costs", "Route rules", "Review & run"])

    with facilities:
        st.caption("On + Optimize: the solver may open or close the site. On + Open: it must open and the solver chooses S/M/L. On + S/M/L: that size is required. Off: forced closed.")
        choices_i, choices_g = {}, {}
        for heading, sites, source, target, prefix in (
            ("Integrated plants", DATA["integrated_sites"], p["integrated_choices"], choices_i, "i"),
            ("Split grinders", DATA["split_sites"], p["split_choices"], choices_g, "g")):
            st.markdown(f"**{heading}**")
            for site in sites:
                sid = site["id"]
                label_col, toggle_col, module_col = st.columns([2.5, 1.1, 2.0], vertical_alignment="center")
                label_col.markdown(f"**{sid}** · {site['name']}")
                on = toggle_col.toggle("On / off", value=source[sid] != "Closed",
                                       key=f"site_{prefix}_{sid}_{tag}", label_visibility="collapsed",
                                       help=f"{sid}: turn off to force closure")
                initial = source[sid] if source[sid] != "Closed" else "Optimize"
                choice = module_col.selectbox(f"{sid} module", ["Optimize", "Open", *MODULES],
                                              index=["Optimize", "Open", *MODULES].index(initial),
                                              key=f"module_{prefix}_{sid}_{tag}",
                                              label_visibility="collapsed", disabled=not on)
                target[sid] = choice if on else "Closed"

    with markets:
        st.caption("Each row shows the selected preset demand and the adjusted demand together. When Scenario A is selected, its demand is the Preset Mt value; there is no second Scenario A demand to enter. Use ▲/▼ or type a percentage.")
        head = st.columns([.65, 1.65, 1.1, 2.1, 1.2])
        for col, label in zip(head, ("Market", "Centre", "Preset Mt", "Change %", "New Mt")):
            col.markdown(f"**{label}**")
        demands=[]
        for j, market in enumerate(DATA["markets"]):
            sid=market["id"]
            cols=st.columns([.65, 1.65, 1.1, 2.1, 1.2], vertical_alignment="center")
            cols[0].write(sid)
            cols[1].write(market["centre"])
            cols[2].write(f"{p['demand_mt'][j]:.3f}")
            pct_key=f"demand_pct_{tag}_{sid}"
            st.session_state.setdefault(pct_key, 0.0)
            down, number, up=cols[3].columns([.7, 1.8, .7], vertical_alignment="center")
            if down.button("▼", key=f"demand_down_{tag}_{sid}", help=f"Decrease {sid} demand change by 1 percentage point"):
                st.session_state[pct_key]=max(-100.0, float(st.session_state[pct_key])-1)
            if up.button("▲", key=f"demand_up_{tag}_{sid}", help=f"Increase {sid} demand change by 1 percentage point"):
                st.session_state[pct_key]=min(300.0, float(st.session_state[pct_key])+1)
            change=number.number_input(f"{sid} change %", -100.0, 300.0, step=1.0,
                key=pct_key, label_visibility="collapsed", format="%.1f")
            adjusted=float(p["demand_mt"][j])*(1+change/100)
            cols[4].markdown(f"**{adjusted:.3f}**")
            demands.append(adjusted)
        st.metric("New total demand", f"{sum(demands):.3f} Mt",
                  f"{sum(demands)-sum(p['demand_mt']):+.3f} Mt vs selected preset")

    with capacities:
        st.caption("Change rated nameplate capacity by site and process. The 90% planning utilization ceiling (editable in Route rules) applies to these adjusted capacities. Capacity changes do not automatically change module investment or fixed operating cost.")
        with st.expander("Original S / M / L module capacities"):
            light_table([{"Type": "Integrated", "Module": m["id"],
                "Clinker Mtpa": m["clinker_mtpa"], "Grinding Mtpa": m["grinding_mtpa"]}
                for m in DATA["integrated_modules"]] +
                [{"Type": "Split grinder", "Module": m["id"], "Clinker Mtpa": None,
                  "Grinding Mtpa": m["grinding_mtpa"]} for m in DATA["split_modules"]])
        st.markdown("**Integrated plants · percentage change from original nameplate**")
        integrated_cap={}
        for site in DATA["integrated_sites"]:
            sid=site["id"]
            label, clinker_col, grind_col=st.columns([2, 1.2, 1.2], vertical_alignment="center")
            label.write(f"{sid} · {site['name']}")
            ck=clinker_col.number_input(f"{sid} clinker capacity change %", -98.0, 300.0,
                float(p["integrated_clinker_capacity_pct"][sid]), 1.0, key=f"icap_ck_{tag}_{sid}")
            gr=grind_col.number_input(f"{sid} grinding capacity change %", -98.0, 300.0,
                float(p["integrated_grinding_capacity_pct"][sid]), 1.0, key=f"icap_gr_{tag}_{sid}")
            integrated_cap[sid]=(ck,gr)
        st.markdown("**Split grinders · percentage change from original nameplate**")
        split_cap={}
        for site in DATA["split_sites"]:
            sid=site["id"]
            label, adjust=st.columns([2, 1.2], vertical_alignment="center")
            label.write(f"{sid} · {site['name']}")
            split_cap[sid]=adjust.number_input(f"{sid} grinding capacity change %", -98.0, 300.0,
                float(p["split_grinding_capacity_pct"][sid]), 1.0, key=f"gcap_gr_{tag}_{sid}")

    with economics:
        st.subheader("Freight rates")
        st.caption("These are editable ₹ per tonne-kilometre rates. The solver applies them to each legal cement or clinker lane.")
        f1,f2 = st.columns(2)
        with f1:
            cement_rate = st.number_input("Cement freight (₹/t-km)", 0.01, 20., float(p["cement_rate"]), .05,
                                          key=f"cement_{tag}")
        with f2:
            clinker_rate = st.number_input("Clinker freight (₹/t-km)", 0.01, 20., float(p["clinker_rate"]), .05,
                                           key=f"clinker_{tag}")
        st.markdown("**Limestone cost at each integrated plant**")
        lime_rates={}
        for site in DATA["integrated_sites"]:
            sid=site["id"]
            label, original, adjustment, changed=st.columns([2, 1, 1.2, 1], vertical_alignment="center")
            label.write(f"{sid} · {site['name']}")
            original.write(f"Preset ₹{p['limestone_rates'][sid]:.0f}/t")
            change=adjustment.number_input(f"{sid} limestone change %", -100.0, 300.0,
                0.0, 1.0, key=f"lime_change_{tag}_{sid}")
            lime_rates[sid]=p["limestone_rates"][sid]*(1+change/100)
            changed.write(f"New ₹{lime_rates[sid]:.2f}/t")
        st.caption("Limestone is purchased at integrated sites; no separate limestone freight lane is specified in the case.")
        m1,m2 = st.columns(2)
        with m1:
            clinker_factor = st.number_input("Clinker per tonne of cement", .40, 1.20,
                float(p["clinker_factor"]), .01, key=f"factor_{tag}",
                help="Default 0.66 t clinker / t cement. A lower value reduces clinker needed for every tonne of cement.")
        with m2:
            limestone_requirement = st.number_input("Limestone per tonne of clinker", .80, 2.50,
                float(p["limestone_requirement"]), .05, key=f"requirement_{tag}")
        st.markdown("**Module investment and fixed operations**")
        with st.popover("ⓘ What do capex and opex multipliers mean?"):
            st.write("1.00 uses the case costs; 1.20 raises that category's costs by 20%; 0.80 reduces them by 20%. Capex is charged through an annualized capital recovery factor (11% hurdle rate, 20-year asset life). Fixed opex is an annual site cost.")
            module_costs = pd.DataFrame([{"Type":"Integrated", "Module":m["id"], "Capex ₹ cr":m["capex_cr"], "Fixed opex ₹ cr/year":m["fixed_opex_cr_yr"]}
                for m in DATA["integrated_modules"]] +
                [{"Type":"Split grinder", "Module":m["id"], "Capex ₹ cr":m["capex_cr"], "Fixed opex ₹ cr/year":m["fixed_opex_cr_yr"]}
                 for m in DATA["split_modules"]])
            light_table(module_costs.to_dict("records"))
            st.caption("These are the original inputs before applying your multipliers. The final network cost can change by a different percentage because the solver can change module choices and shipments.")
        c1,c2 = st.columns(2)
        with c1:
            capex = st.number_input("Capex multiplier", .10, 3.0, float(p["capex_multiplier"]), .05,
                key=f"capex_{tag}", help="Multiplies each selected module's original investment before annualization. 1.00 = case amount.")
        with c2:
            opex = st.number_input("Fixed opex multiplier", .10, 3.0, float(p["opex_multiplier"]), .05,
                key=f"opex_{tag}", help="Multiplies each selected module's annual fixed operating cost. 1.00 = case amount.")

    with rules:
        util = st.number_input("Maximum planned utilization (0.90 = 90%)", .50, 1.00,
            float(p["utilization"]), .01, key=f"util_{tag}")
        r1,r2 = st.columns(2)
        with r1:
            cem_limit = st.number_input("Max cement lane (km)", 100, 2500,
                                        int(p["cement_limit_km"]), 50, key=f"cemlimit_{tag}")
        with r2:
            klink_limit = st.number_input("Max clinker lane (km)", 100, 3000,
                                          int(p["clinker_limit_km"]), 50, key=f"klinklimit_{tag}")
        st.caption("A route beyond its lane limit is excluded from the optimization. All markets still must receive their full target demand.")

    with review:
        st.subheader("Review, name and run the complete scenario")
        st.write("The lock applies to all five decision sections together. It does not solve or save anything. After locking, use Save and Optimize as separate actions.")
        name = st.text_input("Name this scenario", value=f"Custom from {starting}", key=f"scenario_name_{tag}", help="This exact name will appear in Saved scenarios and Scenario comparison after you save.")
        cfg=copy.deepcopy(p)
        safe_name=name.strip() or "Custom"
        if safe_name in PRESET_LABELS:
            safe_name=f"Custom: {safe_name}"
        cfg.update(name=safe_name, origin_preset=starting, cement_rate=cement_rate, clinker_rate=clinker_rate,
            clinker_factor=clinker_factor, limestone_requirement=limestone_requirement,
            capex_multiplier=capex, opex_multiplier=opex, utilization=util,
            cement_limit_km=cem_limit, clinker_limit_km=klink_limit, demand_mt=demands,
            integrated_choices=choices_i, split_choices=choices_g, limestone_rates=lime_rates,
            integrated_clinker_capacity_pct={sid:float(change[0]) for sid,change in integrated_cap.items()},
            integrated_grinding_capacity_pct={sid:float(change[1]) for sid,change in integrated_cap.items()},
            split_grinding_capacity_pct={sid:float(change) for sid,change in split_cap.items()})
        draft_json=json.dumps(cfg,sort_keys=True)
        st.divider()
        st.subheader("Finalize this scenario")
        if st.button("1 · Lock decisions",type="primary",width="stretch",key="lock_decisions"):
            try:
                validate_config(cfg,DATA)
            except (ValueError, KeyError) as exc:
                st.error(str(exc))
            else:
                st.session_state.locked_json=draft_json
                st.session_state.last_lock=f"Locked: {safe_name}"
                st.rerun()
        locked_json=st.session_state.get("locked_json")
        locked=locked_json==draft_json
        if locked:
            st.success(f"Decisions locked for {safe_name}. You can optimize and save this exact set of inputs below.")
            run_col,save_col=st.columns(2)
            run=run_col.button("2 · Optimize locked scenario",type="primary",width="stretch",key="run_locked")
            save=save_col.button("Save named scenario",width="stretch",key="save_locked")
            if save:
                if safe_name in st.session_state.saved_custom and st.session_state.saved_custom[safe_name]!=cfg:
                    st.error("This name is already saved. Change the scenario name, lock again, then save.")
                else:
                    st.session_state.saved_custom[safe_name]=copy.deepcopy(cfg)
                    st.session_state.compare_custom=list(dict.fromkeys(
                        [*st.session_state.get("compare_custom",[]),safe_name]))
                    st.session_state.last_save=f"Saved {safe_name}. It is selected in Scenario comparison."
                    st.rerun()
            if run:
                try:
                    candidate=solve_config(json.loads(locked_json))
                except (ValueError, AssertionError) as exc:
                    st.error(str(exc))
                else:
                    st.session_state.active_json=locked_json
                    st.session_state.active_result=candidate
                    st.session_state.last_run=f"{safe_name}: {status_label(candidate)}"
                    st.rerun()
        elif locked_json:
            st.info("The draft changed after the previous lock. Review your inputs and press Lock decisions again before optimizing or saving.")
        else:
            st.info("The solver has not run on this draft. Finish editing, then lock decisions to enable Optimize and Save.")
        if st.session_state.get("last_run"):
            st.success(st.session_state.last_run + " · See Executive view for the result.")
        if st.session_state.get("last_save"):
            st.success(st.session_state.last_save)
        st.caption("Locking is a snapshot, not an optimization run. Any edit after locking invalidates the lock. Saved scenarios remain available during this browser session; export them from Saved scenarios for later use.")


def render_scenario_library() -> None:
    st.subheader("Scenario library")
    st.write("Inspect the exact assumptions behind a preset or a named scenario. Save a draft in Decision studio after locking it; then select it in Scenario comparison.")
    saved=st.session_state.saved_custom
    options=[*PRESET_LABELS,*saved]
    if st.session_state.get("scenario_detail_name") not in options:
        st.session_state.scenario_detail_name="Base"
    chosen=st.selectbox("Scenario to inspect",options,key="scenario_detail_name")
    cfg=preset(chosen,DATA) if chosen in PRESET_LABELS else saved[chosen]
    origin=cfg.get("origin_preset", "Base") if chosen not in PRESET_LABELS else "Base"
    if origin not in PRESET_LABELS:
        origin="Base"
    reference=preset(origin,DATA)
    st.caption(("Case preset" if chosen in PRESET_LABELS else "Your saved scenario")+
               f" · Red cells differ from {origin}.")
    st.metric("Demand",f"{sum(cfg['demand_mt']):.3f} Mt")
    def site_rows(c: dict) -> list[dict]:
        return ([{"Site":s["id"],"Location":s["name"],"Decision":c["integrated_choices"][s["id"]]}
                 for s in DATA["integrated_sites"]] +
                [{"Site":s["id"],"Location":s["name"],"Decision":c["split_choices"][s["id"]]}
                 for s in DATA["split_sites"]])
    def demand_rows(c: dict) -> list[dict]:
        return [{"Market":m["id"],"Centre":m["centre"],"Demand Mt":round(c["demand_mt"][j],5)}
                for j,m in enumerate(DATA["markets"])]
    def rate_rows(c: dict) -> list[dict]:
        return [{"Input":key,"Value":value} for key,value in (
            ("Cement freight ₹/t-km",c["cement_rate"]),
            ("Clinker freight ₹/t-km",c["clinker_rate"]),
            ("Clinker factor t/t cement",c["clinker_factor"]),
            ("Limestone t/t clinker",c["limestone_requirement"]),
            ("Capex multiplier",c["capex_multiplier"]),
            ("Fixed opex multiplier",c["opex_multiplier"]),
            ("Max utilization %",round(100*c["utilization"],1)),
            ("Max cement lane km",c["cement_limit_km"]),
            ("Max clinker lane km",c["clinker_limit_km"]))]
    def site_cost_rows(c: dict) -> list[dict]:
        return ([{"Site":sid,"Limestone ₹/t":c["limestone_rates"][sid],
            "Clinker capacity %":c["integrated_clinker_capacity_pct"][sid],
            "Grinding capacity %":c["integrated_grinding_capacity_pct"][sid]} for sid in I]
            + [{"Site":sid,"Limestone ₹/t":"—","Clinker capacity %":"—",
                "Grinding capacity %":c["split_grinding_capacity_pct"][sid]} for sid in G])
    st.markdown("**Site decisions**")
    light_table(site_rows(cfg),site_rows(reference))
    st.markdown("**Demand by market**")
    light_table(demand_rows(cfg),demand_rows(reference))
    st.markdown("**Rates, efficiency and route limits**")
    light_table(rate_rows(cfg),rate_rows(reference))
    st.markdown("**Site limestone rates and nameplate changes**")
    light_table(site_cost_rows(cfg),site_cost_rows(reference))
    if chosen in saved:
        if st.button(f"Delete {chosen}",key="delete_saved"):
            del saved[chosen]
            st.session_state.compare_custom=[x for x in st.session_state.get("compare_custom",[]) if x!=chosen]
            st.session_state.pop("comparison_rows",None)
            st.session_state.pop("comparison_results",None)
            st.rerun()
    st.divider()
    st.markdown("**Keep your named scenarios after this browser session**")
    st.download_button("Export saved scenarios (JSON)",json.dumps(saved,indent=2,sort_keys=True),
        file_name="rookie_saved_scenarios.json",mime="application/json")
    incoming=st.file_uploader("Import a previously exported scenario file",type=["json"],key="scenario_import")
    if incoming is not None and st.button("Import named scenarios"):
        try:
            payload=json.loads(incoming.getvalue().decode("utf-8"))
            if not isinstance(payload,dict):
                raise ValueError("Expected a JSON object of named scenarios.")
            for scenario_name,settings in payload.items():
                if scenario_name in PRESET_LABELS or not isinstance(settings,dict) or settings.get("name")!=scenario_name:
                    raise ValueError(f"Invalid or reserved scenario name: {scenario_name}")
                validate_config(settings,DATA)
                if scenario_name in saved and saved[scenario_name]!=settings:
                    raise ValueError(f"{scenario_name} already exists with different settings. Delete it before importing.")
        except (ValueError,KeyError,TypeError,UnicodeDecodeError) as exc:
            st.error(f"Import failed: {exc}")
        else:
            saved.update(payload)
            st.success(f"Imported {len(payload)} named scenario(s).")
            st.rerun()


if "saved_custom" not in st.session_state:
    st.session_state.saved_custom={}
if "active_json" not in st.session_state:
    st.session_state.active_json=BASE_JSON
if "active_result" not in st.session_state:
    st.session_state.active_result=solve_cached(BASE_JSON)

baseline=solve_cached(BASE_JSON)
active=st.session_state.active_result
st.markdown('<div class="eyebrow">PRESCRIPTIVE ANALYTICS  ·  FY2030</div>',unsafe_allow_html=True)
title_col,help_col=st.columns([7,1],vertical_alignment="center")
title_col.title("The Rookie | Cement Network Lab")
with help_col:
    method=st.popover("ⓘ Model guide",use_container_width=True)
st.markdown('<p class="intro">Use the Decision studio to change facilities, capacity, prices, material efficiency and market demand. The MILP reoptimizes clinker and cement flows, explains the new footprint, and tests whether the original Base modules still work.</p>',unsafe_allow_html=True)

view,studio,library,modes,compare,sensitivity,network=st.tabs(["Executive view","Decision studio","Saved scenarios","Network choices","Scenario comparison","Sensitivity lab","Network explorer"])
with view:
    st.subheader(f"Current decision: {active['name']}")
    render_solution(active,baseline)
    st.download_button("Download scenario settings (JSON)",st.session_state.active_json,
                       file_name="rookie_scenario.json",mime="application/json")
with studio:
    render_decision_studio()
with library:
    render_scenario_library()
with modes:
    scenario=json.loads(st.session_state.active_json)
    st.subheader(f"Compare network choices · {scenario['name']}")
    st.write("This view compares three decisions: (1) keep Base facility sizes and reroute, (2) keep Base locations but resize modules, or (3) choose a new network. It evaluates all three under the same scenario inputs.")
    st.write("Each mode uses the same demand, material rates, freight rates, route rules and capacity ceiling. Only the facility choices change.")
    labels=["1 · Reroute Base modules","2 · Resize Base locations","3 · Redesign"]
    mode_results={
        labels[0]:solve_config(fixed_base_config(scenario,baseline)),
        labels[1]:solve_config(resize_base_config(scenario,baseline)),
        labels[2]:active,
    }
    st.caption("Scenario closures apply to every choice. A required site/module in the Decision studio applies to full redesign; the first two choices hold the Base footprint as described above.")
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
        st.plotly_chart(cost_bridge(ref,redesign,ref_label),width="stretch",key="mode_bridge",theme=None)
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
    st.session_state.compare_custom=[n for n in st.session_state.get("compare_custom",[]) if n in custom_names]
    extra=st.multiselect("Your saved custom scenarios",custom_names,key="compare_custom")
    st.caption("Lock and save a named scenario in Decision studio to add it here. Inspect or delete it in Saved scenarios.")
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
                              paper_bgcolor="#f6fafb",plot_bgcolor="#f6fafb",
                              template="plotly_white",font={"family":"Arial","color":"#183344"})
            st.plotly_chart(fig,width="stretch",theme=None)
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
    st.caption("Set a low and high value for this one assumption. The app will test evenly spaced values between them, optimizing the entire network each time. Other inputs remain as in the current scenario.")
    range_col,upper_col,points_col=st.columns(3)
    with range_col:
        lower=st.number_input("From",min_value=float(low),max_value=float(high),
            value=float(max(low,round(center*.8,2))),step=.01,help="Lowest value to test")
    with upper_col:
        upper=st.number_input("To",min_value=float(low),max_value=float(high),
            value=float(min(high,round(center*1.2,2))),step=.01,help="Highest value to test")
    with points_col:
        points=st.selectbox("Number of solves",[5,7,9],index=1,
            help="The number of fresh optimization runs at evenly spaced input values. More solves give a smoother curve and take longer.")
    st.caption(f"Example: {points} solves test {points} values from {lower:g} to {upper:g}, including both endpoints. This is an analysis of one input, separate from the Decision studio's main Optimize button.")
    if lower>=upper:
        st.warning("Set 'To' above 'From' to run the sensitivity analysis.")
    if st.button("Run sensitivity",type="primary",disabled=lower>=upper):
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
                              paper_bgcolor="#f6fafb",plot_bgcolor="#f6fafb",
                              template="plotly_white",font={"family":"Arial","color":"#183344"})
            st.plotly_chart(fig,width="stretch",theme=None)
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
            st.plotly_chart(make_sankey(flows,"Finished cement: production site to market (Mt)","Mt","rgba(8,115,110,.27)"),width="stretch",theme=None)
            st.dataframe(pd.DataFrame(flows).sort_values("mt",ascending=False).rename(columns={"source":"From","target":"Market","mt":"Mt","km":"km"}),
                         hide_index=True,width="stretch")
            st.download_button("Download cement routes (CSV)",pd.DataFrame(flows).to_csv(index=False).encode("utf-8-sig"),
                               "cement_routes.csv","text/csv")
        with ck:
            flows=active["clinker_flows"]
            if flows:
                st.plotly_chart(make_sankey(flows,"Clinker: integrated plant to split grinder (Mt)","Mt","rgba(24,59,77,.29)"),width="stretch",theme=None)
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
