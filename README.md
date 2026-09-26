# The Rookie | Cement Network Lab

An interactive FY2030 network design case study. A mixed-integer linear program (MILP) chooses integrated plants and split grinding modules, routes clinker and cement, and minimizes annual relevant cost while meeting every market's demand.

**Live demo:** add the Streamlit Community Cloud URL after deployment.

## What a user can do

- Start from the Base plan or seven alternative presets: regional demand mix (A), freight shock (B), I1 delay (C), I3 limestone cost (D), G1 closure, 600 km cement lanes, and 10% demand growth.
- Close any integrated plant or grinder, require a specific S/M/L module, or leave its size to the solver.
- Edit all 12 market demands, six site limestone rates, cement and clinker freight rates, clinker factor, limestone consumption, utilization ceiling, permitted distances, and capex/opex multipliers.
- Compare reoptimized scenarios with the original Base and test whether the **fixed Base modules** can still meet demand under each scenario.
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

## Model

Binary variables choose at most one module per site. Nonnegative flows represent I→M cement, I→G clinker, and G→M cement. The objective sums annualized investment (11% hurdle rate, 20-year life), fixed operating costs, site-specific limestone costs, cement freight, and clinker freight. Flow balance serves each market exactly; split grinder clinker receipts equal `clinker_factor × cement output`; integrated clinker and grinding, and split grinding, stay within the chosen utilization ceiling. Lanes exceeding the chosen distance cap are excluded.

The data in `data/case_data.json` is extracted from the supplied teaching case's **2030 Demand**, **Candidate Facilities**, **Planning Distances**, and **Scenarios & Deliverables** worksheets. `scripts/extract_case_data.py` documents this extraction. No live logistics, demand forecast, or external price data is used. Scenario cost differences change assumptions, so they are not causal savings from changing the network. The fixed-module penalty, when feasible, compares two networks under *identical* scenario conditions.

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

A GitHub account with repository permission and a Streamlit account are needed to publish. There are no secrets or API keys in the app.

## Interview story

> I formulated a cement plant and distribution decision as a MILP, translated spreadsheet case inputs into an auditable solver, and built a Streamlit decision interface. The app runs closures, freight and material scenarios, exposes network and cost changes, and distinguishes a new optimum from the robustness of the original installed capacity. I validated the Base and four workbook scenarios against Excel. I would extend it with probabilistic demand and implementation timing before using it for a real capital decision.

This project demonstrates operations research, numerical validation, product design, scenario analysis, and communication to nontechnical decision makers. It does not claim a predictive AI model.
