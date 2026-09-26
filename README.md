# The Rookie | Cement Network Lab

An interactive FY2030 network design case study. A mixed-integer linear program (MILP) chooses integrated plants and split grinding modules, routes clinker and cement, and minimizes annual relevant cost while meeting every market's demand.

**Live demo:** add your Streamlit Community Cloud URL after deployment.

## What a user can do

- Start from the Base plan or seven alternative presets: regional demand mix (A), freight shock (B), I1 delay (C), I3 limestone cost (D), G1 closure, 600 km cement lanes, and 10% demand growth.
- Use the full-width **Decision studio** to turn each integrated plant or split grinder on/off, require a specific S/M/L module, require an open site with optimizable size, or let the solver decide whether to open it. An off switch forces closure; an on switch with Optimize merely makes the site available.
- Change the 12 market demands and six limestone rates by percentage from the selected preset. Each market shows its selected-preset and adjusted demand on the same row; ▲/▼ buttons change demand by one percentage point. Scenario A demand is loaded automatically when that preset is selected.
- Change rated nameplate clinker and integrated grinding capacities separately for each integrated site, plus rated grinding capacity for each split grinder, by percentage. These adjustments affect MILP capacity constraints and reported utilization; module capex and opex stay as separately controlled assumptions.
- Edit cement and clinker freight rates, clinker factor, limestone consumption, utilization ceiling, permitted distances, and capex/opex multipliers. The cost info popover lists original module capex and annual fixed opex and explains annualization.
- Find the freight inputs in **Decision studio → Freight & costs**. Make changes in any of the five input sections, then go to **Review & run** to give the scenario a name and press the single **Lock decisions** button. Locking validates and snapshots *all five sections together*; it does not run the solver. Any later edit invalidates the lock and requires another lock. Use **Save named scenario** to add that locked configuration to Scenario comparison, and **Optimize locked scenario** to run the MILP.
- Compare reoptimized scenarios with the original Base and test whether the **fixed Base modules** can still meet demand under each scenario.
- Compare three decisions under the same scenario inputs in **Network choices**: reroute with Base modules, resize at Base locations, and redesign the footprint. Inspect a cost bridge and exact facility changes.
- Inspect every preset and saved configuration in **Saved scenarios**, including site decisions, market demand, cost and route settings. Values changed from the scenario's originating preset are highlighted red. Delete named scenarios there. Names are saved for the current browser session; export/import the JSON scenario collection to use them later.
- See an executive summary, facility choices, cost composition, cement and clinker route diagrams, utilization, and feasibility explanations. Download settings and results as JSON/CSV.
- Run a one-variable sensitivity sweep and inspect discrete changes in the investment footprint.

## Reproducible case benchmarks

| Scenario | Annual relevant cost (₹ crore) |
| --- | ---: |
| Base | 7,792.261 |
| A · Demand mix | 7,889.444 |
| B · Freight shock | 8,518.148 |
| C · I1 delay | 8,215.102 |
| D · I3 limestone | 7,859.642 |

These match the assignment workbook to within ₹0.001 crore. The Base design opens I1 L, I3 L, I4 L, I5 M, I6 S; G1 L, G2 M, G3 M, G4 M; and leaves I2 closed. Its annual demand is 33.78 Mt. Under C, the same installed Base modules with I1 removed cannot serve all demand; a new investment decision is required.

The decision modes clarify what changes are needed. Under A, rerouting with fixed Base modules costs ₹7,974.880 crore; resizing at Base locations achieves ₹7,889.444 crore, equal to full redesign. Under C, neither rerouting nor resizing at Base locations can meet demand when I1 is unavailable; the feasible redesign opens I2. These are like-for-like mode comparisons because all modes use the same scenario prices and demand.

## Model

Binary variables choose at most one module per site, or exactly one when the user requires that location open. Nonnegative flows represent I→M cement, I→G clinker, and G→M cement. The objective sums annualized investment (11% hurdle rate, 20-year life), fixed operating costs, site-specific limestone costs, cement freight, and clinker freight. Flow balance serves each market exactly; split grinder clinker receipts equal `clinker_factor × cement output`; integrated clinker and grinding, and split grinding, stay within the chosen utilization ceiling. Lanes exceeding the chosen distance cap are excluded.

The data in `data/case_data.json` is extracted from the supplied teaching case's **2030 Demand**, **Candidate Facilities**, **Planning Distances**, and **Scenarios & Deliverables** worksheets. `scripts/extract_case_data.py` documents this extraction. No live logistics, demand forecast, or external price data is used. Scenario cost differences change assumptions, so they are not causal savings from changing the network. The fixed-module penalty, when feasible, compares two networks under *identical* scenario conditions. User-entered capacity changes scale nameplate but do not estimate an engineering or investment cost for that capacity change.

The solver is SciPy `milp` (HiGHS) with a 0.01% relative MIP gap target. Results are labeled if the time limit expires before certification. The code reconciles cost components, all 12 market balances, and selected-site capacity after each solve. This is **prescriptive optimization**, not a machine-learning model; the explanatory text is derived from model outputs and does not call a language model.

## Run locally

Use Python 3.12. From this directory:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run validation:

```bash
python -m unittest discover -s tests -v
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload the **contents of this directory** to its root. Include `app.py`, `model.py`, `data/case_data.json`, `requirements.txt`, `.streamlit/config.toml`, and the other source files. Keep the relative paths.
2. In Streamlit Community Cloud, create a new app from that repository. Choose the main branch and entrypoint `app.py`.
3. In Advanced settings, select Python 3.12 if it is not the default. The Python package versions are pinned in `requirements.txt`.
4. Deploy, open the public app URL, and compare its Base cost with ₹7,792.261 crore. Add the URL to this README and your assignment submission.

Upload `.streamlit/config.toml` at the **repository root**, including its leading dot. The app uses a light canvas, light controls with dark text, teal action buttons with white text, and teal selection states. Scenario controls live in Decision studio rather than the sidebar. The small **Model guide** popover beside the title contains the MILP and interview notes.

A GitHub account with repository permission and a Streamlit account are needed to publish. There are no secrets or API keys in the app.

## Interview story

> I formulated a cement plant and distribution decision as a MILP, translated spreadsheet case inputs into an auditable solver, and built a Streamlit decision interface. The app runs closures, freight and material scenarios, exposes network and cost changes, and distinguishes a new optimum from the robustness of the original installed capacity. I validated the Base and four workbook scenarios against Excel. I would extend it with probabilistic demand and implementation timing before using it for a real capital decision.

This project demonstrates operations research, numerical validation, product design, scenario analysis, and communication to nontechnical decision makers. It does not claim a predictive AI model.
