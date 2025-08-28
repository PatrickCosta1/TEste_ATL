import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from advanced_product_selector import AdvancedProductSelector

selector = AdvancedProductSelector()

answers = {
    'localizacao': 'exterior',
    'domotica': False,
    'tipo_piscina': 'skimmer',
    'revestimento': 'tela',
    'luz': 'monofasica',
    'casa_maquinas_abaixo': 'nao',
    'tipo_luzes': 'branco_frio',
    'tratamento_agua': 'nao'
}

metrics = {'m3_h': 16, 'volume': 50}

dimensions = {'comprimento': 8, 'largura': 4, 'prof_min': 1.2, 'prof_max': 1.5, 'volume': 50}

budget = selector.generate_budget(answers, metrics, dimensions)

print('Families in budget:')
for k in budget['families'].keys():
    print('-', k)

filtracao = budget['families'].get('Filtração') or budget['families'].get('Filtracao') or budget['families'].get('Filtração ')
print('\nFiltração items:')
if filtracao:
    for key, item in filtracao.items():
        pid = item.get('product_id')
        alt = item.get('alternative_to')
        print(f"{key}: {item['name']} x{item['quantity']} - {item['item_type']} | product_id={pid} alternative_to={alt}")
        # debug full item on duplicates
        # print(item)
else:
    print('Nenhuma entrada encontrada na família Filtração.')

print('\nTotals:')
print(budget['family_totals'].get('Filtração'))
print('Total price:', budget['total_price'])
