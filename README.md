# The Rookie | Cement Network Lab

**A mixed-integer optimisation model and interactive Streamlit app for designing India's FY2030 cement production and distribution network.**

The model decides **where to build** integrated cement plants and split grinding units, **what size** (S / M / L) each one should be, and **how to route** clinker and cement between them and 12 demand markets. It does this at the **minimum annual relevant cost** while serving every market's demand exactly.

> Originally created by [rahul31809](https://github.com/rahul31809/Supply-Chain-Network-Design-Model) as a teaching-case solution.

---

## Contents

1. [The business problem](#1-the-business-problem)
2. [Network structure](#2-network-structure)
3. [Input data](#3-input-data)
4. [Mathematical formulation](#4-mathematical-formulation)
   - [Sets and indices](#41-sets-and-indices)
   - [Parameters](#42-parameters)
   - [Decision variables](#43-decision-variables)
   - [Objective function](#44-objective-function)
   - [Constraints, explained one by one](#45-constraints-explained-one-by-one)
   - [User-controlled site decisions](#46-user-controlled-site-decisions-as-constraints)
   - [Model size](#47-model-size)
5. [Solver and built-in validation](#5-solver-and-built-in-validation)
6. [Scenarios](#6-scenarios)
7. [Results](#7-results)
8. [Three ways to respond to a scenario](#8-three-ways-to-respond-to-a-scenario-reroute-resize-redesign)
9. [The app](#9-the-app)
10. [Assumptions and limitations](#10-assumptions-and-limitations)
11. [Project structure](#11-project-structure)
12. [Run locally](#12-run-locally)
13. [Deploy on Streamlit Community Cloud](#13-deploy-on-streamlit-community-cloud)

---

## 1. The business problem

Cement production happens in two stages:

1. **Clinker production (kiln):** limestone is quarried and burned in a kiln to make *clinker*. This has to happen near a limestone deposit, so these plants are tied to mining belts.
2. **Grinding:** clinker is ground with gypsum and other additives (fly ash, slag) to make *cement*. Grinding can happen at the kiln site or at a separate *split grinding unit* closer to customers.

Cement is bulky and cheap per tonne, so **freight is a large share of total cost**. The network designer faces a trade-off:

| Option | Benefit | Cost |
|---|---|---|
| Grind at the integrated plant and ship cement | No second facility needed | Long, expensive cement hauls to distant markets |
| Ship clinker to a split grinder near the market | Clinker freight is cheaper per t·km, and only ~0.66 t of clinker is needed per tonne of cement | Extra capex and fixed opex for the grinding unit |

The model finds the best balance of these options for a single steady-state year, FY2030.

---

## 2. Network structure

```
  Limestone belts               Split grinding units           Demand markets
  (integrated plants)           (near consumption)

   I1 … I6  ──── clinker (z) ────►  G1 … G4  ──── cement (x^G) ───►  M1 … M12
      │                                                                  ▲
      └─────────────────────── cement (x^I) ─────────────────────────────┘
```

Three types of flow are allowed:

| Flow | From → To | Material | Variable |
|---|---|---|---|
| Direct cement | Integrated plant → Market | Cement | $x^{I}_{im}$ |
| Clinker transfer | Integrated plant → Split grinder | Clinker | $z_{ig}$ |
| Split cement | Split grinder → Market | Cement | $x^{G}_{gm}$ |

The network does **not** allow plant-to-plant, grinder-to-grinder or market-to-market transfers, and it has no external clinker purchases.

---

## 3. Input data

All inputs live in [`data/case_data.json`](data/case_data.json). They were extracted from the teaching case workbook's **2030 Demand**, **Candidate Facilities**, **Planning Distances** and **Scenarios & Deliverables** sheets. [`scripts/extract_case_data.py`](scripts/extract_case_data.py) documents the extraction.

### 3.1 Markets (12), with base demand totalling 33.78 Mt

| ID | Cluster | Centre | Base demand (Mt) |
|---|---|---|---:|
| M1 | Delhi NCR / Upper North | Delhi NCR | 3.995 |
| M2 | Rajasthan | Jaipur | 1.900 |
| M3 | Uttar Pradesh | Lucknow | 3.400 |
| M4 | Madhya Pradesh | Bhopal | 1.745 |
| M5 | Gujarat | Ahmedabad | 1.860 |
| M6 | Maharashtra & Goa | Pune | 3.900 |
| M7 | Bihar & Jharkhand | Patna | 2.800 |
| M8 | West Bengal & North-East | Kolkata | 3.050 |
| M9 | Odisha & Chhattisgarh | Bhubaneswar | 3.085 |
| M10 | Andhra Pradesh & Telangana | Hyderabad | 3.100 |
| M11 | Karnataka & Kerala | Bengaluru | 2.500 |
| M12 | Tamil Nadu | Chennai | 2.445 |

### 3.2 Candidate integrated plant sites (6)

| ID | Limestone belt | State | Limestone cost (₹/t) |
|---|---|---|---:|
| I1 | Chittorgarh–Nimbahera | Rajasthan | 205 |
| I2 | Kachchh / Bhuj | Gujarat | 225 |
| I3 | Satna–Rewa | Madhya Pradesh | 195 |
| I4 | Baloda Bazar–Raipur | Chhattisgarh | 200 |
| I5 | Kurnool–Kadapa | Andhra Pradesh | 210 |
| I6 | Kalaburagi–Wadi | Karnataka | 215 |

### 3.3 Candidate split grinding sites (4)

| ID | Location | Region |
|---|---|---|
| G1 | Dadri / Greater Noida | NCR |
| G2 | Pune | Maharashtra |
| G3 | Sankrail / Kolkata | West Bengal |
| G4 | Chennai | Tamil Nadu |

### 3.4 Module options

Each site can host **at most one** module size. The annual fixed charge equals annualised capex plus fixed opex (see §4.4).

**Integrated plant modules**

| Size | Clinker capacity (Mtpa) | Grinding capacity (Mtpa) | Capex (₹ cr) | Fixed opex (₹ cr/yr) | Annual fixed charge (₹ cr/yr) |
|---|---:|---:|---:|---:|---:|
| S | 3.0 | 2.5 | 2,500 | 90 | 403.94 |
| M | 4.5 | 3.5 | 3,300 | 120 | 534.40 |
| L | 6.0 | 5.0 | 4,200 | 155 | 682.42 |

**Split grinding modules**

| Size | Grinding capacity (Mtpa) | Capex (₹ cr) | Fixed opex (₹ cr/yr) | Annual fixed charge (₹ cr/yr) |
|---|---:|---:|---:|---:|
| S | 2.5 | 700 | 28 | 115.90 |
| M | 4.0 | 1,000 | 38 | 163.58 |
| L | 6.0 | 1,500 | 55 | 243.36 |

Larger modules have lower cost per tonne of capacity (economies of scale), which pushes the solver toward fewer, larger sites. Freight costs push the other way.

### 3.5 Global parameters (defaults)

| Parameter | Value | Meaning |
|---|---:|---|
| Hurdle rate $r$ | 11% | Cost of capital used to annualise capex |
| Asset life $n$ | 20 years | Annualisation horizon |
| Max utilisation $u$ | 90% | Usable share of nameplate capacity |
| Clinker factor $\alpha$ | 0.66 | Tonnes of clinker per tonne of cement |
| Limestone requirement $\beta$ | 1.5 | Tonnes of limestone per tonne of clinker |
| Cement freight $f^{C}$ | ₹3.03 / t·km | Road/rail cement haulage rate |
| Clinker freight $f^{K}$ | ₹1.60 / t·km | Bulk clinker haulage rate |
| Cement lane cap $D^{C}$ | 800 km | Longest permitted cement lane |
| Clinker lane cap $D^{K}$ | 1,300 km | Longest permitted clinker lane |

Distances are planning-centroid distances (km) in three matrices: integrated→market (6×12), grinder→market (4×12) and integrated→grinder (6×4).

---

## 4. Mathematical formulation

The model is a **mixed-integer linear program (MILP)**. Flows are in **Mt/year** and costs are in **₹ crore/year**.

### 4.1 Sets and indices

| Symbol | Set |
|---|---|
| $i \in I$ | Integrated plant sites, I1–I6 |
| $g \in G$ | Split grinding sites, G1–G4 |
| $m \in M$ | Markets, M1–M12 |
| $k \in K = \{S, M, L\}$ | Module sizes |
| $A^{IM} \subseteq I \times M$ | Permitted direct cement lanes: $d_{im} \le D^{C}$ |
| $A^{GM} \subseteq G \times M$ | Permitted split cement lanes: $d_{gm} \le D^{C}$ |
| $A^{IG} \subseteq I \times G$ | Permitted clinker lanes: $d_{ig} \le D^{K}$ |

### 4.2 Parameters

| Symbol | Meaning |
|---|---|
| $D_m$ | Cement demand of market $m$ (Mt) |
| $d_{im}, d_{gm}, d_{ig}$ | Lane distances (km) |
| $f^{C}, f^{K}$ | Cement and clinker freight rates (₹/t·km) |
| $c_i$ | Limestone cost at integrated site $i$ (₹/t) |
| $\alpha$ | Clinker factor (t clinker / t cement) |
| $\beta$ | Limestone requirement (t limestone / t clinker) |
| $u$ | Maximum utilisation (fraction of nameplate) |
| $K^{I}_{k}, P^{I}_{k}$ | Clinker and grinding nameplate of integrated module $k$ (Mtpa) |
| $P^{G}_{k}$ | Grinding nameplate of split module $k$ (Mtpa) |
| $\delta^{K}_i, \delta^{P}_i, \delta^{G}_g$ | User capacity adjustments (fraction, default 0) |
| $CAPEX_k, OPEX_k$ | Module capex (₹ cr) and fixed opex (₹ cr/yr) |
| $\mu^{cap}, \mu^{op}$ | Capex and opex multipliers (default 1) |
| $CRF$ | Capital recovery factor |

### 4.3 Decision variables

| Variable | Type | Meaning |
|---|---|---|
| $y^{I}_{ik} \in \{0,1\}$ | Binary | 1 if integrated site $i$ is built with module $k$ |
| $y^{G}_{gk} \in \{0,1\}$ | Binary | 1 if split grinding site $g$ is built with module $k$ |
| $x^{I}_{im} \ge 0$ | Continuous | Cement shipped from integrated plant $i$ to market $m$ (Mt) |
| $x^{G}_{gm} \ge 0$ | Continuous | Cement shipped from split grinder $g$ to market $m$ (Mt) |
| $z_{ig} \ge 0$ | Continuous | Clinker shipped from integrated plant $i$ to split grinder $g$ (Mt) |

Flow variables are only created for permitted lanes. A lane longer than the distance cap has **no variable at all**, so it cannot carry flow.

### 4.4 Objective function

Minimise the total annual relevant cost:

$$
\min Z \;=\; \underbrace{\sum_{i,k}F^{I}_{k}\,y^{I}_{ik} + \sum_{g,k}F^{G}_{k}\,y^{G}_{gk}}_{\text{fixed: annualised capex + opex}}
\;+\; \underbrace{0.1\sum_{(i,m)}\big(f^{C}d_{im} + \alpha\beta c_i\big)\,x^{I}_{im}}_{\text{direct cement freight + limestone}}
\;+\; \underbrace{0.1\sum_{(i,g)}\big(f^{K}d_{ig} + \beta c_i\big)\,z_{ig}}_{\text{clinker freight + limestone}}
\;+\; \underbrace{0.1\sum_{(g,m)} f^{C}d_{gm}\,x^{G}_{gm}}_{\text{split cement freight}}
$$

**Fixed charge per module.** Capex is converted into an equivalent annual payment with the capital recovery factor:

$$
CRF = \frac{r(1+r)^n}{(1+r)^n - 1} = \frac{0.11 \cdot 1.11^{20}}{1.11^{20}-1} \approx 0.12558
$$

$$
F_k = \mu^{cap}\cdot CRF \cdot CAPEX_k \;+\; \mu^{op}\cdot OPEX_k
$$

**The 0.1 factor.** Flows are in Mt and rates are in ₹/t, so one Mt at ₹1/t equals ₹10⁶, which is ₹0.1 crore. Multiplying by 0.1 converts every variable cost into ₹ crore.

**Limestone cost is attached to flows.** Each tonne of cement shipped directly from plant $i$ uses $\alpha$ t of clinker, which needs $\alpha\beta$ t of limestone at cost $c_i$. Each tonne of clinker shipped to a grinder needs $\beta$ t of limestone. Because the model charges limestone on the outbound flows, it never needs a separate production variable. Limestone price differences between belts directly change which plant is cheapest to source from.

The model excludes costs that are identical in every feasible design, such as gypsum, power and variable grinding cost, if they are uniform. That is why the objective is called *relevant* cost.

### 4.5 Constraints, explained one by one

#### C1. At most one module per site

$$
\sum_{k \in K} y^{I}_{ik} \le 1 \quad \forall i \in I \qquad\qquad \sum_{k \in K} y^{G}_{gk} \le 1 \quad \forall g \in G
$$

A site is either closed (all $y = 0$) or built with exactly one size. It cannot host both an S and an L module. If the user selects **Open** for a site, the inequality becomes $= 1$ (see §4.6).

#### C2. Demand satisfaction for every market

$$
\sum_{i:(i,m)\in A^{IM}} x^{I}_{im} \;+\; \sum_{g:(g,m)\in A^{GM}} x^{G}_{gm} \;=\; D_m \quad \forall m \in M
$$

Every market receives **exactly** its demand, combining direct shipments from integrated plants and shipments from split grinders. There is no unmet demand variable and no over-supply. If demand can't be met, the model is **infeasible** rather than silently short-shipping, and the app reports a diagnostic explaining why.

#### C3. Integrated plant grinding capacity

$$
\sum_{m:(i,m)\in A^{IM}} x^{I}_{im} \;\le\; u \sum_{k} P^{I}_{k}\,(1+\delta^{P}_i)\; y^{I}_{ik} \quad \forall i \in I
$$

Cement ground at integrated plant $i$, which is everything it ships directly to markets, cannot exceed usable grinding capacity. This constraint also **links flow to investment**: if site $i$ is closed, the right side is 0, so no cement can leave it.

#### C4. Integrated plant clinker capacity

$$
\alpha \sum_{m} x^{I}_{im} \;+\; \sum_{g} z_{ig} \;\le\; u \sum_{k} K^{I}_{k}\,(1+\delta^{K}_i)\; y^{I}_{ik} \quad \forall i \in I
$$

The kiln must produce two things: clinker for its own grinding mill ($\alpha$ t per tonne of direct cement) **plus** all clinker shipped to split grinders. Together they must fit within usable kiln capacity. This is often the binding constraint, because a plant's kiln capacity (e.g. 6.0 Mtpa for L) supports more cement than its own mill can grind (5.0 Mtpa). The surplus clinker is what feeds the split grinders.

#### C5. Clinker balance at split grinders

$$
\sum_{i:(i,g)\in A^{IG}} z_{ig} \;=\; \alpha \sum_{m:(g,m)\in A^{GM}} x^{G}_{gm} \quad \forall g \in G
$$

Split grinders have no kiln. Every tonne of cement they ship must be backed by exactly $\alpha$ tonnes of clinker received from integrated plants. Conservation is exact: the model has no clinker stockpile and no external clinker purchase.

#### C6. Split grinder grinding capacity

$$
\sum_{m} x^{G}_{gm} \;\le\; u \sum_{k} P^{G}_{k}\,(1+\delta^{G}_g)\; y^{G}_{gk} \quad \forall g \in G
$$

Cement output at a split grinder must fit within usable grinding capacity. Like C3, this forces $x^{G}_{gm}=0$ when the grinder is not built.

#### C7. Lane-distance policy

$$
x^{I}_{im} \text{ exists only if } d_{im} \le D^{C}, \qquad
x^{G}_{gm} \text{ exists only if } d_{gm} \le D^{C}, \qquad
z_{ig} \text{ exists only if } d_{ig} \le D^{K}
$$

This is a service and logistics policy constraint: cement must not travel more than 800 km, and clinker not more than 1,300 km. The model enforces it by **pre-filtering** lanes rather than adding a constraint row. With the defaults, 26 of 72 direct-cement lanes, 14 of 48 split-cement lanes and 15 of 24 clinker lanes are permitted. Tightening the cap (scenario F) removes lanes and can force new facilities.

#### C8. Variable domains

$$
y^{I}_{ik},\, y^{G}_{gk} \in \{0,1\}, \qquad x^{I}_{im},\, x^{G}_{gm},\, z_{ig} \ge 0
$$

All flows are nonnegative, and facility decisions are all-or-nothing.

#### Why the utilisation ceiling matters

Every capacity constraint (C3, C4, C6) multiplies nameplate by $u = 0.9$. That leaves 10% headroom for maintenance shutdowns, seasonal peaks and ramp-up. Because no plant can be planned above 90%, the network needs more installed capacity than demand alone would require. In the Base solution, several sites run at exactly 90%, so this ceiling is binding.

### 4.6 User-controlled site decisions as constraints

For each site, the app lets the user override the solver. Each choice is implemented as variable bounds or a tightened C1:

| Choice | Implementation | Effect |
|---|---|---|
| **Optimize** (default) | No extra constraint | Solver decides whether to open the site and what size to use |
| **Open** | C1 becomes $\sum_k y_{\cdot k} = 1$ | Site must be built; solver picks S, M or L |
| **S / M / L** | Lower bound $y_{\cdot k}=1$; other sizes have upper bound 0 | Site is built with exactly that module |
| **Closed** | Upper bound $y_{\cdot k}=0$ for all $k$ | Site cannot be built, so all its flows are forced to 0 by C3/C4/C6 |

The app also exposes these inputs, which change the parameters (not the structure) of the model:

- 12 market demands $D_m$
- six limestone rates $c_i$
- freight rates $f^{C}, f^{K}$
- $\alpha$, $\beta$, $u$
- lane caps $D^{C}, D^{K}$
- capex/opex multipliers
- per-site capacity adjustments $\delta$, between −99% and +300%

Capacity adjustments scale nameplate only. They do **not** change the module's capex or opex.

### 4.7 Model size

| Component | Count |
|---|---:|
| Binary variables ($y^I$, $y^G$) | 30 (10 sites × 3 sizes) |
| Continuous flow variables (default lane caps) | 55 (26 + 14 + 15) |
| Constraint rows | 42 (10 module + 12 demand + 6 kiln + 6 integrated grinding + 4 clinker balance + 4 split grinding) |

The model is small enough that HiGHS proves optimality in well under a second for each scenario.

---

## 5. Solver and built-in validation

- **Solver:** SciPy [`milp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html), backed by the HiGHS branch-and-cut solver, with a **0.01% relative MIP gap** target and a configurable time limit (default 60 s). If the time limit expires before optimality is proven, the result is labelled `incumbent` instead of `optimal`.
- **Post-solve checks** (in `model.solve`). Every solution is independently re-verified, and the code raises an error if any check fails:
  1. **Cost reconciliation:** fixed + limestone + cement freight + clinker freight, recomputed from the flows, must equal the solver's objective within 10⁻⁴.
  2. **Market balance:** delivered cement must equal demand in all 12 markets within 10⁻⁵ Mt.
  3. **Capacity:** no selected site may exceed the utilisation ceiling.
- **Infeasibility diagnostics:** when no feasible network exists, `_capacity_diagnostic` compares the maximum usable grinding and clinker capacity (assuming every allowed site at its largest permitted module) against required demand and clinker. It then explains which one falls short.
- **Regression tests** (`tests/test_model.py`): the Base case and scenarios A–D are checked against the Excel workbook to ±₹0.001 crore, along with the fixed-module infeasibility under C, the ordering of the three decision modes, site-choice behaviour and other invariants.

---

## 6. Scenarios

| Preset | Change from Base | Purpose |
|---|---|---|
| **Base** | None | Original FY2030 plan |
| **A · Demand mix** | Market demands replaced with the regional-shift forecast (East and Central up, West and South down) | Required case scenario |
| **B · Freight shock** | Cement ₹3.03 → ₹3.75/t·km; clinker ₹1.60 → ₹1.85/t·km | Required case scenario |
| **C · I1 delay** | I1 (Chittorgarh) forced Closed | Required case scenario |
| **D · I3 limestone** | I3 limestone ₹195 → ₹300/t | Optional case scenario |
| **E · G1 closure** | G1 (Dadri) forced Closed | Management stress test |
| **F · 600 km cement** | Cement lane cap 800 → 600 km | Policy stress test |
| **G · 10% demand** | All market demands ×1.10 | Growth stress test |

---

## 7. Results

All figures were reproduced by running `model.solve` on each preset.

| Scenario | Annual cost (₹ cr) | Δ vs Base | Integrated plants (I1–I6) | Split grinders (G1–G4) |
|---|---:|---:|---|---|
| **Base** | **7,792.261** | — | L · – · L · L · M · S | L · M · M · M |
| A · Demand mix | 7,889.444 | +97.2 | L · – · L · L · S · M | L · M · L · S |
| B · Freight shock | 8,518.148 | +725.9 | L · – · L · L · M · M | L · M · M · S |
| C · I1 delay | 8,215.102 | +422.8 | – · S · L · L · M · L | L · M · L · S |
| D · I3 limestone | 7,859.642 | +67.4 | L · – · L · L · M · M | L · M · M · S |
| E · G1 closure | 8,796.183 | +1,003.9 | L · S · L · L · L · – | – · L · L · M |
| F · 600 km cement | 7,831.077 | +38.8 | L · – · L · M · M · M | L · M · L · S |
| G · 10% demand | 8,599.258 | +807.0 | L · – · L · L · M · L | L · M · L · S |

"–" means the site is closed. Scenarios A–D match the assignment workbook to within ₹0.001 crore.

### Base-case cost breakdown

| Component | ₹ crore/yr | Share |
|---|---:|---:|
| Annualised capex + fixed opex | 3,719.68 | 47.7% |
| Cement freight | 2,444.69 | 31.4% |
| Clinker freight | 946.57 | 12.1% |
| Limestone | 681.31 | 8.7% |
| **Total** | **7,792.26** | 100% |

Other Base-case results:

- **Split grinding share:** 44% of cement is ground at split units close to markets.
- **Average haul:** cement lead is ≈ 239 km and clinker lead is ≈ 602 km. The network deliberately moves long-distance volume as clinker, which is cheaper per t·km and lighter per tonne of cement, and keeps cement hauls short.
- **Utilisation:** the busiest sites hit the 90% ceiling, so capacity is binding.

### Key insights

- **I2 (Kachchh) stays closed** in the Base case. It has the most expensive limestone (₹225/t), and Gujarat demand can be served from I1. I2 only opens when another source disappears (C, E).
- **G1 (Dadri) is the most valuable single asset.** Closing it raises cost by ₹1,004 cr/yr, more than any other scenario. NCR is the largest market and is far from every limestone belt.
- **The freight shock is the largest external cost driver** (+9.3%). The footprint barely changes, because freight is already minimised; the cost mostly passes through.
- **A tighter cement-lane policy is cheap** (+0.5%). The solver shifts volume to split grinders by upsizing G3 and rebalancing plant sizes.

---

## 8. Three ways to respond to a scenario: reroute, resize, redesign

Each scenario's new optimum shows what you would build with hindsight. But the Base network will already have been built. The app separates three levels of response, all evaluated with the **same** scenario prices and demand, so the comparison is like-for-like:

| Mode | What stays fixed | What can change | Function |
|---|---|---|---|
| **Reroute** | Every Base module (site and size) | Flows only | `fixed_base_config` |
| **Resize** | Which Base sites are open or closed | Module size at open sites, plus flows | `resize_base_config` |
| **Redesign** | Nothing | Full footprint, sizes and flows | `solve(scenario)` |

Since each mode relaxes the previous one, cost(Reroute) ≥ cost(Resize) ≥ cost(Redesign). The tests assert this ordering. An explicitly closed site in a scenario stays closed in every mode.

| Scenario | Reroute | Resize | Redesign |
|---|---:|---:|---:|
| A · Demand mix | 7,974.880 | 7,889.444 | 7,889.444 |
| C · I1 delay | **Infeasible** | **Infeasible** | 8,215.102 (opens I2) |

**How to read this:**

- **Scenario A.** Keeping the Base modules costs ₹85 cr/yr more than the optimum. Resizing at the existing sites recovers all of that, so no new site is needed.
- **Scenario C.** Without I1, the Base footprint can't serve 33.78 Mt even when resized. The diagnostic reports a grinding shortfall. A new investment (opening I2) is required.

---

## 9. The app

`app.py` is a Streamlit interface around the model.

- **Presets.** Start from Base or any of the seven alternatives.
- **Decision studio.** Set each site to ● ON / ○ OFF, force a specific S/M/L module, require a site to be open while letting the solver size it, or leave it to Optimize. Here you can also adjust:
  - market demand (±% per market, with ▲/▼ for 1-point steps)
  - limestone rates
  - per-site capacity
  - freight rates under **Freight & costs**
  - clinker factor, limestone consumption, utilisation ceiling, lane caps, and capex/opex multipliers
- **Review & run.** Name the scenario and press **Lock decisions**, which validates and snapshots all five input sections together. Any later edit invalidates the lock. Then use **Optimize locked scenario** to run the MILP, and **Save named scenario** to add the scenario to the comparison.
- **Scenario comparison.** Compare reoptimised scenarios against Base, and test whether the fixed Base modules can still meet demand.
- **Network choices.** See Reroute / Resize / Redesign side by side, with a cost bridge and exact facility changes.
- **Saved scenarios.** Inspect every preset and saved configuration. Values that differ from the originating preset are highlighted in red. Scenarios can be deleted here, and the whole collection can be exported or imported as JSON.
- **Results views:**
  - executive summary and facility choices
  - cost composition
  - cement and clinker route diagrams
  - utilisation and feasibility explanations
  - JSON/CSV downloads
- **Sensitivity sweep.** Vary one parameter over a range and watch where the investment footprint changes.

All explanatory text in the app is computed from model output. No language model is called.

---

## 10. Assumptions and limitations

- **Single period and deterministic.** The model designs one steady-state year (FY2030) with known demand. It does not cover phasing, construction lead times or demand uncertainty.
- **Linear freight.** Cost is rate × distance × tonnes, using centroid distances rather than real routes. There are no mode choices (rail/road/sea), backhaul effects or volume discounts.
- **Discrete sizes only.** Each site has S, M or L, and at most one module.
- **Capacity adjustments are free.** User capacity adjustments change nameplate without changing capex or opex, so they show what-if capacity effects, not costed expansion options.
- **Uniform costs are omitted.** Costs that are the same in every design are left out. The objective is for comparing designs, not a full P&L.
- **Assumption-driven differences.** Scenario cost differences come from changed assumptions; they are not savings achieved by redesigning the network. Only the Reroute/Resize/Redesign comparison isolates the value of a network decision under identical conditions.
- **Prescriptive, not predictive.** This is operations research, not machine learning, and it makes no forecasts.

---

## 11. Project structure

```
.
├── app.py                      Streamlit user interface
├── model.py                    MILP formulation, scenario presets, validation
├── data/
│   └── case_data.json          Markets, sites, modules, distances, defaults
├── scripts/
│   └── extract_case_data.py    Workbook → JSON extraction (documentation)
├── tests/
│   └── test_model.py           Regression tests vs Excel and model invariants
├── requirements.txt            Pinned Python dependencies
└── .devcontainer/              GitHub Codespaces / VS Code dev container
```

---

## 12. Run locally

Requires Python 3.11 or newer (3.12 recommended).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

Use the model directly from Python:

```python
from model import load_case, base_config, preset, solve

data = load_case()
result = solve(base_config(data), data)
print(result["objective_cr"])          # 7792.26...
print(result["integrated_modules"])    # {'I1': 'L', 'I2': 'Closed', ...}

shock = solve(preset("B · Freight shock", data), data)
print(shock["cost_breakdown_cr"])
```

The repository also includes a dev container. Opening it in **GitHub Codespaces** installs the dependencies and starts the app on port 8501 automatically.

---

## 13. Deploy on Streamlit Community Cloud

1. In [Streamlit Community Cloud](https://share.streamlit.io), create a new app from this repository.
2. Select the `main` branch and set the entrypoint to `app.py`.
3. Under *Advanced settings*, choose Python 3.12. Package versions are pinned in `requirements.txt`.
4. Deploy, open the app and check that the Base cost reads **₹7,792.261 crore**.

The app needs no secrets or API keys.
