#!/usr/bin/env python3
# Teste rápido para verificar formatação de quantidades

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

# Teste com dados que geram quantidades decimais
dimensions = {
    'comprimento': 7.5,  # Valor decimal
    'largura': 3.8,      # Valor decimal  
    'prof_min': 1.2,     # Valor decimal
    'prof_max': 1.8      # Valor decimal
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
    'zona_praia_largura': 1.5,   # Valor decimal
    'zona_praia_comprimento': 2.3, # Valor decimal
    'escadas': 'sim',
    'escadas_largura': 0.8,      # Valor decimal
    'localidade': 'Porto'
}

print("🧮 Teste de Formatação de Quantidades")
print("=" * 50)

# Calcular métricas
calc = PoolCalculator()
metrics = calc.calculate_all_metrics(
    dimensions['comprimento'], 
    dimensions['largura'], 
    dimensions['prof_min'], 
    dimensions['prof_max']
)
print(f"✓ Dimensões: {dimensions['comprimento']}x{dimensions['largura']}x{dimensions['prof_min']}-{dimensions['prof_max']}")
print(f"✓ Volume: {metrics['volume']:.2f} m³")

# Gerar orçamento
selector = AdvancedProductSelector()
budget = selector.generate_budget(answers, metrics, dimensions)

# Verificar família construção
if 'construcao' in budget['families']:
    construcao = budget['families']['construcao']
    print(f"\n🏗️  Família Construção: {len(construcao)} produtos")
    print("-" * 40)
    
    for key, item in construcao.items():
        qty = item['quantity']
        # Mostrar como apareceria no template
        qty_formatted = f"{qty:.2f}"
        print(f"• {item['name'][:25]:.<25} {qty_formatted:>8} {item['unit']:>4}")
        
    # Mostrar total da família
    total = budget['family_totals'].get('construcao', 0)
    print(f"\n💰 Total Construção: €{total:.2f}")
else:
    print("❌ Família construção não encontrada")

print(f"\n📊 Total Geral: €{budget['total_price']:.2f}")
