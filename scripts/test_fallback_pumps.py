import sys, os
# Ensure project root is on sys.path so imports work when running the script directly
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from advanced_product_selector import AdvancedProductSelector

# Forcing fallback-only by pointing DB path to a non-existing file
# But the selector's DatabaseManager will create DB if missing; instead we directly call selector functions

selector = AdvancedProductSelector()
# Prepare conditions and metrics that require a pump
conditions = {'power_type': 'monofasica', 'domotics': 'false', 'location': 'exterior'}
metrics = {'m3_h': 16, 'volume': 50}

# Call internal pump selection
pumps = selector._get_suitable_pumps(metrics['m3_h'], conditions['power_type'])

print('Found pumps:')
for p in pumps:
    cap = p['attributes'].get('Capacidade')
    if isinstance(cap, dict):
        cap_val = cap.get('value')
    else:
        cap_val = cap
    print(f"- {p['id']} {p['name']} | capacity={cap_val} | fase={p['attributes'].get('Fase')} | tipo={p['attributes'].get('Tipo Bomba')} | item_type={p.get('item_type')}")
