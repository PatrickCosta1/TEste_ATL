#!/usr/bin/env python3
"""
Teste para verificar se os cálculos da laje estão corretos após a correção
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_calculo_corrigido():
    """Testa se o cálculo da laje está correto com 10m² e 10cm"""
    
    print("=== TESTE: CÁLCULO CORRIGIDO DA LAJE ===\n")
    
    # Inicializar componentes
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Dados de teste: 10m² com 10cm de espessura
    dimensions = {
        'comprimento': 5.0,
        'largura': 2.0,
        'prof_min': 1.0,
        'prof_max': 2.0
    }
    
    # Calcular métricas
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'],
        dimensions['largura'],
        dimensions['prof_min'],
        dimensions['prof_max']
    )
    
    print(f"Teste com laje de 10m² e espessura 10cm")
    print(f"Esperado: valor razoável (não €11,833)")
    print()
    
    # Teste com apenas pavimento
    answers_pavimento = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 10.0,
        'laje_espessura': 10,  # 10cm (valor que vem do formulário)
        'revestimento_laje': 'nao'
    }
    
    budget_pavimento = selector.generate_budget(answers_pavimento, metrics, dimensions)
    laje_products = budget_pavimento.get('families', {}).get('construcao_laje', {})
    
    print("=== APENAS PAVIMENTO ===")
    for product_id, product in laje_products.items():
        print(f"Produto: {product['name'][:80]}...")
        print(f"Preço: €{product['price']}")
        print(f"Cálculo: {product['reasoning']}")
    
    # Cálculo manual para verificação
    laje_m2 = 10.0
    laje_espessura_cm = 10
    laje_espessura_m = laje_espessura_cm / 100  # 0.10m
    laje_m3 = laje_m2 * laje_espessura_m  # 10 × 0.10 = 1.0m³
    
    # Fórmula: (70 × m³ + 10 × m²) × 100/60
    preco_custo = 70 * laje_m3 + 10 * laje_m2  # 70 × 1.0 + 10 × 10 = 170
    preco_venda = preco_custo * 100 / 60  # 170 × 100/60 = 283.33
    
    print(f"\n=== VERIFICAÇÃO MANUAL ===")
    print(f"Área: {laje_m2}m²")
    print(f"Espessura: {laje_espessura_cm}cm = {laje_espessura_m}m")
    print(f"Volume: {laje_m3}m³")
    print(f"Preço custo: (70 × {laje_m3} + 10 × {laje_m2}) = {preco_custo}")
    print(f"Preço venda: {preco_custo} × 100/60 = €{preco_venda:.2f}")
    
    # Verificar se o preço calculado está correto
    pavimento_product = next((p for p in laje_products.values() if 'pavimento' in p['name'].lower()), None)
    if pavimento_product:
        calculado = pavimento_product['price']
        print(f"\nResultado do sistema: €{calculado}")
        if abs(calculado - preco_venda) < 0.01:
            print("✅ CORRETO: Cálculo está certo!")
        else:
            print(f"❌ ERRO: Esperado €{preco_venda:.2f}, obtido €{calculado}")
    else:
        print("❌ ERRO: Produto de pavimento não encontrado")
    
    print("\n" + "="*50)
    
    # Teste com revestimento também
    print("\n=== COM REVESTIMENTO (GRANITO VILA REAL) ===")
    answers_completo = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 10.0,
        'laje_espessura': 10,  # 10cm
        'revestimento_laje': 'sim',
        'material_revestimento': 'granito_vila_real'  # €35/m²
    }
    
    budget_completo = selector.generate_budget(answers_completo, metrics, dimensions)
    laje_products_comp = budget_completo.get('families', {}).get('construcao_laje', {})
    
    total_familia = 0
    for product_id, product in laje_products_comp.items():
        subtotal = product['price'] * product['quantity']
        total_familia += subtotal
        print(f"- {product['name'][:60]}...")
        print(f"  Preço: €{product['price']} × {product['quantity']} = €{subtotal}")
        print(f"  Cálculo: {product['reasoning']}")
        print()
    
    print(f"Total da família: €{total_familia:.2f}")
    
    # Cálculo manual do revestimento
    # Fórmula: (15 + 13 + preço_material) × m² × 100/60
    preco_material = 35.0  # Granito Vila Real
    preco_rev_custo = (15 + 13 + preco_material) * laje_m2  # (15+13+35) × 10 = 630
    preco_rev_venda = preco_rev_custo * 100 / 60  # 630 × 100/60 = 1050
    
    print(f"\n=== VERIFICAÇÃO REVESTIMENTO ===")
    print(f"Preço material: €{preco_material}/m²")
    print(f"Preço custo: (15 + 13 + {preco_material}) × {laje_m2} = {preco_rev_custo}")
    print(f"Preço venda: {preco_rev_custo} × 100/60 = €{preco_rev_venda:.2f}")
    
    total_esperado = preco_venda + preco_rev_venda  # 283.33 + 1050 = 1333.33
    print(f"\nTotal esperado: €{preco_venda:.2f} + €{preco_rev_venda:.2f} = €{total_esperado:.2f}")
    
    if abs(total_familia - total_esperado) < 0.01:
        print("✅ CORRETO: Total da família está certo!")
    else:
        print(f"❌ ERRO: Esperado €{total_esperado:.2f}, obtido €{total_familia:.2f}")

if __name__ == "__main__":
    test_calculo_corrigido()
