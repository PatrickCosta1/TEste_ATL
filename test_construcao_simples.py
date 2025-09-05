#!/usr/bin/env python3
# Script simples para testar família Construção

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

# Dados de teste
dimensions = {
    'comprimento': 8.0,
    'largura': 4.0,
    'prof_min': 1.0,
    'prof_max': 2.0
}

answers = {
    'acesso': 'facil',
    'escavacao': False,
    'forma': 'retangular',
    'tipo_piscina': 'skimmer',
    'revestimento': 'tela',
    'domotica': False,
    'localizacao': 'exterior',
    'luz': 'monofasica',
    'zona_praia': 'sim',
    'zona_praia_largura': 2.0,
    'zona_praia_comprimento': 4.0,
    'escadas': 'sim',
    'escadas_largura': 1.0,
    'localidade': 'Viseu'
}

# Teste
print("🔧 Teste Construção da Piscina")
print("=" * 50)

# 1. Calcular métricas
calc = PoolCalculator()
metrics = calc.calculate_all_metrics(
    dimensions['comprimento'], 
    dimensions['largura'], 
    dimensions['prof_min'], 
    dimensions['prof_max']
)
print(f"✓ Métricas: volume={metrics['volume']}, m3_massa={metrics['m3_massa']}")

# 2. Gerar orçamento completo
selector = AdvancedProductSelector()
try:
    budget = selector.generate_budget(answers, metrics, dimensions)
    print(f"✓ Famílias geradas: {list(budget['families'].keys())}")
    
    if 'construcao' in budget['families']:
        construcao = budget['families']['construcao']
        print(f"✓ Família Construção: {len(construcao)} produtos")
        total = 0
        for key, item in construcao.items():
            price = item['price'] * item['quantity']
            total += price
            print(f"  - {item['name']}: {item['quantity']} {item['unit']} @ €{item['price']} = €{price:.2f}")
        print(f"✓ Total Construção: €{total:.2f}")
    else:
        print("❌ Família 'construcao' não encontrada!")
        print(f"   Famílias disponíveis: {list(budget['families'].keys())}")
        
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
