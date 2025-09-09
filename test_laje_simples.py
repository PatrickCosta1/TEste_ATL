#!/usr/bin/env python3
"""
Teste simples da função de seleção de produtos da laje
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector

def test_laje_function():
    """Testa apenas a função _select_laje_products"""
    
    print("=== TESTE SIMPLES: FUNÇÃO _select_laje_products ===\n")
    
    selector = AdvancedProductSelector()
    
    # Teste 1: Sem laje
    print("--- TESTE 1: Sem laje ---")
    answers1 = {'havera_laje': 'nao'}
    dimensions1 = {'comprimento': 8, 'largura': 4}
    
    result1 = selector._select_laje_products(answers1, dimensions1)
    print(f"Resultado: {len(result1)} produtos")
    print(f"Esperado: 0 produtos")
    print(f"Status: {'✓ CORRETO' if len(result1) == 0 else '❌ ERRO'}\n")
    
    # Teste 2: Com laje apenas pavimento
    print("--- TESTE 2: Com laje, apenas pavimento ---")
    answers2 = {
        'havera_laje': 'sim',
        'laje_m2': 50.0,
        'laje_espessura': 0.15,  # 15cm
        'revestimento_laje': 'nao'
    }
    dimensions2 = {'comprimento': 8, 'largura': 4}
    
    result2 = selector._select_laje_products(answers2, dimensions2)
    print(f"Resultado: {len(result2)} produtos")
    
    if len(result2) > 0:
        for product_id, product in result2.items():
            print(f"  - {product['name'][:60]}...")
            print(f"    Preço: €{product['price']}")
            print(f"    Cálculo: {product['reasoning']}")
    
    print(f"Esperado: 1 produto (pavimento)")
    print(f"Status: {'✓ CORRETO' if len(result2) == 1 else '❌ ERRO'}\n")
    
    # Teste 3: Com laje e revestimento
    print("--- TESTE 3: Com laje e revestimento ---")
    answers3 = {
        'havera_laje': 'sim',
        'laje_m2': 50.0,
        'laje_espessura': 0.15,  # 15cm
        'revestimento_laje': 'sim',
        'material_revestimento': 'granito_preto_angola'  # €90/m²
    }
    dimensions3 = {'comprimento': 8, 'largura': 4}
    
    result3 = selector._select_laje_products(answers3, dimensions3)
    print(f"Resultado: {len(result3)} produtos")
    
    if len(result3) > 0:
        for product_id, product in result3.items():
            print(f"  - {product['name'][:60]}...")
            print(f"    Preço: €{product['price']}")
            print(f"    Cálculo: {product['reasoning']}")
    
    print(f"Esperado: 2 produtos (pavimento + revestimento)")
    print(f"Status: {'✓ CORRETO' if len(result3) == 2 else '❌ ERRO'}\n")
    
    # Teste 4: Verificar cálculos
    print("--- TESTE 4: Verificação de cálculos ---")
    
    # Cálculo esperado para pavimento (50m² × 15cm):
    # m³ = 50 × 0.15 = 7.5
    # Custo = 70 × 7.5 + 10 × 50 = 525 + 500 = 1025
    # Venda = 1025 × 100/60 = 1708.33
    expected_pavimento = 1708.33
    
    if 'pavimento_terreo' in result3:
        actual_pavimento = result3['pavimento_terreo']['price']
        print(f"Pavimento - Esperado: €{expected_pavimento:.2f}, Calculado: €{actual_pavimento:.2f}")
        print(f"Pavimento: {'✓ CORRETO' if abs(actual_pavimento - expected_pavimento) < 0.01 else '❌ ERRO'}")
    
    # Cálculo esperado para revestimento (50m² com granito angola €90/m²):
    # Custo = (15 + 13 + 90) × 50 = 118 × 50 = 5900
    # Venda = 5900 × 100/60 = 9833.33
    expected_revestimento = 9833.33
    
    if 'revestimento_laje' in result3:
        actual_revestimento = result3['revestimento_laje']['price']
        print(f"Revestimento - Esperado: €{expected_revestimento:.2f}, Calculado: €{actual_revestimento:.2f}")
        print(f"Revestimento: {'✓ CORRETO' if abs(actual_revestimento - expected_revestimento) < 0.01 else '❌ ERRO'}")
    
    print("\n=== FIM DO TESTE ===")

if __name__ == "__main__":
    test_laje_function()
