#!/usr/bin/env python3
"""
Script de teste para a nova família "Construção da Laje"
Testa a lógica completa do questionário à seleção de produtos e cálculo de preços
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_laje_construction():
    """Testa a implementação completa da construção da laje"""
    
    print("=== TESTE: CONSTRUÇÃO DA LAJE ===\n")
    
    # Inicializar componentes
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Dados de teste (piscina 8x4m)
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
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
    
    print(f"Dimensões da piscina: {dimensions['comprimento']}x{dimensions['largura']}m")
    print(f"Métricas calculadas: {metrics}\n")
    
    # Teste 1: Sem laje (não deve adicionar produtos)
    print("--- TESTE 1: Sem construção de laje ---")
    answers_sem_laje = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'nao'
    }
    
    budget_sem_laje = selector.generate_budget(answers_sem_laje, metrics, dimensions)
    laje_products_sem = budget_sem_laje.get('families', {}).get('construcao_laje', {})
    
    print(f"Produtos de laje encontrados: {len(laje_products_sem)}")
    if len(laje_products_sem) == 0:
        print("✓ CORRETO: Nenhum produto de laje adicionado quando havera_laje = 'nao'\n")
    else:
        print("❌ ERRO: Produtos de laje foram adicionados quando não deviam\n")
    
    # Teste 2: Com laje, apenas pavimento
    print("--- TESTE 2: Com laje, apenas pavimento ---")
    answers_laje_pavimento = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 50.0,
        'laje_espessura': 0.15,
        'revestimento_laje': 'nao'
    }
    
    budget_laje_pavimento = selector.generate_budget(answers_laje_pavimento, metrics, dimensions)
    laje_products_pav = budget_laje_pavimento.get('families', {}).get('construcao_laje', {})
    
    print(f"Produtos de laje encontrados: {len(laje_products_pav)}")
    for product_id, product in laje_products_pav.items():
        print(f"  - {product['name']}: {product['quantity']} {product.get('unit', 'un')} × €{product['price']} = €{product['quantity'] * product['price']}")
        if 'reasoning' in product:
            print(f"    Cálculo: {product['reasoning']}")
    
    # Verificar se o preço está correto
    expected_pavimento_price = (70 * 50 * 0.15 + 10 * 50) * 100 / 60  # (70×m³×espessura + 10×m²) × 100/60
    expected_pavimento_price = round(expected_pavimento_price, 2)
    
    pavimento_product = next((p for p in laje_products_pav.values() if 'pavimento' in p['name'].lower()), None)
    if pavimento_product:
        actual_price = pavimento_product['price']
        print(f"Preço esperado pavimento: €{expected_pavimento_price}")
        print(f"Preço calculado pavimento: €{actual_price}")
        if abs(actual_price - expected_pavimento_price) < 0.01:
            print("✓ CORRETO: Preço do pavimento calculado corretamente\n")
        else:
            print("❌ ERRO: Preço do pavimento incorreto\n")
    else:
        print("❌ ERRO: Produto de pavimento não encontrado\n")
    
    # Teste 3: Com laje e revestimento (pedra natural)
    print("--- TESTE 3: Com laje e revestimento (pedra natural) ---")
    answers_laje_completa = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 50.0,
        'laje_espessura': 0.15,
        'revestimento_laje': 'sim',
        'material_revestimento': 'calcario_moca_creme'  # €45/m²
    }
    
    budget_laje_completa = selector.generate_budget(answers_laje_completa, metrics, dimensions)
    laje_products_comp = budget_laje_completa.get('families', {}).get('construcao_laje', {})
    
    print(f"Produtos de laje encontrados: {len(laje_products_comp)}")
    for product_id, product in laje_products_comp.items():
        print(f"  - {product['name']}: {product['quantity']} {product.get('unit', 'un')} × €{product['price']} = €{product['quantity'] * product['price']}")
        if 'reasoning' in product:
            print(f"    Cálculo: {product['reasoning']}")
    
    # Verificar preços
    expected_revestimento_price = (15 + 13 + 45) * 50 * 100 / 60  # (15+13+material_price) × m² × 100/60
    expected_revestimento_price = round(expected_revestimento_price, 2)
    
    revestimento_product = next((p for p in laje_products_comp.values() if 'revestimento' in p['name'].lower()), None)
    if revestimento_product:
        actual_rev_price = revestimento_product['price']
        print(f"Preço esperado revestimento: €{expected_revestimento_price}")
        print(f"Preço calculado revestimento: €{actual_rev_price}")
        if abs(actual_rev_price - expected_revestimento_price) < 0.01:
            print("✓ CORRETO: Preço do revestimento calculado corretamente")
        else:
            print("❌ ERRO: Preço do revestimento incorreto")
    else:
        print("❌ ERRO: Produto de revestimento não encontrado")
    
    # Verificar se tanto pavimento quanto revestimento estão presentes
    has_pavimento = any('pavimento' in p['name'].lower() for p in laje_products_comp.values())
    has_revestimento = any('revestimento' in p['name'].lower() for p in laje_products_comp.values())
    
    if has_pavimento and has_revestimento:
        print("✓ CORRETO: Ambos pavimento e revestimento presentes\n")
    else:
        print("❌ ERRO: Pavimento ou revestimento em falta\n")
    
    # Teste 4: Com revestimento cerâmico
    print("--- TESTE 4: Com revestimento cerâmico ---")
    answers_laje_ceramica = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 30.0,
        'laje_espessura': 0.12,
        'revestimento_laje': 'sim',
        'material_revestimento': 'ceramica_portuguesa'  # €40/m²
    }
    
    budget_laje_ceramica = selector.generate_budget(answers_laje_ceramica, metrics, dimensions)
    laje_products_cer = budget_laje_ceramica.get('families', {}).get('construcao_laje', {})
    
    print(f"Produtos de laje encontrados: {len(laje_products_cer)}")
    for product_id, product in laje_products_cer.items():
        print(f"  - {product['name']}: {product['quantity']} {product.get('unit', 'un')} × €{product['price']} = €{product['quantity'] * product['price']}")
        if 'reasoning' in product:
            print(f"    Cálculo: {product['reasoning']}")
    
    # Verificar se o material cerâmico está sendo identificado corretamente
    ceramica_product = next((p for p in laje_products_cer.values() if 'cerâmica' in p['name'].lower()), None)
    if ceramica_product:
        print("✓ CORRETO: Produto cerâmico identificado corretamente\n")
    else:
        print("❌ ERRO: Produto cerâmico não identificado\n")
    
    print("=== FIM DOS TESTES ===")

if __name__ == "__main__":
    test_laje_construction()
