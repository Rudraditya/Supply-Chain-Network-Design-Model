"""Extract teaching-case inputs from the supplied Excel workbook into deployable JSON."""
import json
import sys
from pathlib import Path
import openpyxl

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
w = openpyxl.load_workbook(source, data_only=True, read_only=True)
demand, facilities, distances, scenarios = (w[n] for n in (
    '2030 Demand', 'Candidate Facilities', 'Planning Distances', 'Scenarios & Deliverables'))

def value(sheet, row, col):
    return sheet.cell(row, col).value

payload = {
    'provenance': {
        'case': 'The Rookie — India Cement Network Design, FY2030',
        'source_sheets': ['2030 Demand', 'Candidate Facilities', 'Planning Distances', 'Scenarios & Deliverables'],
        'note': 'Teaching-case inputs. Market centres and distances are planning centroids, not live routes.'
    },
    'markets': [
        {'id': value(demand, r, 1), 'cluster': value(demand, r, 2),
         'region': value(demand, r, 3), 'centre': value(demand, r, 4),
         'base_demand_mt': round(float(value(demand, r, 6)), 6),
         'scenario_a_demand_mt': round(float(value(scenarios, r+7, 3)), 6)}
        for r in range(6, 18)
    ],
    'integrated_sites': [
        {'id': value(facilities, r, 1), 'name': value(facilities, r, 2),
         'state': value(facilities, r, 3), 'limestone_inr_per_t': float(value(facilities, r, 4))}
        for r in range(5, 11)
    ],
    'split_sites': [
        {'id': value(facilities, r, 1), 'name': value(facilities, r, 2),
         'region': value(facilities, r, 3)}
        for r in range(20, 24)
    ],
    'integrated_modules': [
        {'id': value(facilities, r, 1), 'clinker_mtpa': float(value(facilities, r, 2)),
         'grinding_mtpa': float(value(facilities, r, 3)), 'capex_cr': float(value(facilities, r, 4)),
         'fixed_opex_cr_yr': float(value(facilities, r, 5))}
        for r in range(14, 17)
    ],
    'split_modules': [
        {'id': value(facilities, r, 1), 'grinding_mtpa': float(value(facilities, r, 2)),
         'capex_cr': float(value(facilities, r, 3)), 'fixed_opex_cr_yr': float(value(facilities, r, 4))}
        for r in range(27, 30)
    ],
    'distances_km': {
        'integrated_to_market': [[float(value(distances, r, c)) for c in range(2, 14)] for r in range(7, 13)],
        'split_to_market': [[float(value(distances, r, c)) for c in range(2, 14)] for r in range(16, 20)],
        'integrated_to_split': [[float(value(distances, r, c)) for c in range(2, 6)] for r in range(23, 29)]
    },
    'defaults': {
        'hurdle_rate': float(value(facilities, 33, 2)),
        'asset_life_years': int(value(facilities, 34, 2)),
        'max_utilization': float(value(facilities, 36, 2)),
        'clinker_factor': float(value(facilities, 37, 2)),
        'limestone_t_per_t_clinker': float(value(facilities, 38, 2)),
        'cement_freight_inr_per_tkm': float(value(facilities, 39, 2)),
        'clinker_freight_inr_per_tkm': float(value(facilities, 40, 2)),
        'cement_lane_max_km': 800,
        'clinker_lane_max_km': 1300
    }
}
assert abs(sum(m['base_demand_mt'] for m in payload['markets']) - 33.78) < 1e-8
assert abs(sum(m['scenario_a_demand_mt'] for m in payload['markets']) - 33.78) < 1e-8
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
print(destination)
