#!/usr/bin/env python3
"""
Debug específico do problema com revestimento da laje
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector

def debug_laje_revestimento():
    """Debug específico do revestimento da laje"""
    
    print("=== DEBUG: REVESTIMENTO DA LAJE ===\n")
    
    selector = AdvancedProductSelector()
    
    # Testar diferentes cenários
    dimensions = {
        'comprimento': 10.0,
        'largura': 5.0,
        'prof_min': 1.0,
        'prof_max': 2.0,
        'volume': 75.0
    }
    
    test_cases = [
        {
            'name': 'Travertino Navona',
            'answers': {
                'havera_laje': 'sim',
                'laje_m2': 80.0,
                'laje_espessura': 0.20,
                'revestimento_laje': 'sim',
                'material_revestimento': 'travertino_navona'  # Este material NÃO existe na lista!
            }
        },
        {
            'name': 'Travertino Turco (correto)',
            'answers': {
                'havera_laje': 'sim',
                'laje_m2': 80.0,
                'laje_espessura': 0.20,
                'revestimento_laje': 'sim',
                'material_revestimento': 'travertino_turco'  # Este existe
            }
        },
        {
            'name': 'Granito Preto Angola',
            'answers': {
                'havera_laje': 'sim',
                'laje_m2': 80.0,
                'laje_espessura': 0.20,
                'revestimento_laje': 'sim',
                'material_revestimento': 'granito_preto_angola'
            }
        },
        {
            'name': 'Sem revestimento',
            'answers': {
                'havera_laje': 'sim',
                'laje_m2': 80.0,
                'laje_espessura': 0.20,
                'revestimento_laje': 'nao'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- TESTE {i}: {test_case['name']} ---")
        
        # Mostrar configuração
        answers = test_case['answers']
        print("Configuração:")
        for key, value in answers.items():
            if 'laje' in key:
                print(f"  {key}: {value}")
        print()
        
        # Testar função
        laje_products = selector._select_laje_products(answers, dimensions)
        
        print(f"Produtos encontrados: {len(laje_products)}")
        if laje_products:
            for product_id, product in laje_products.items():
                print(f"  - {product_id}: {product['name'][:70]}...")
                print(f"    Preço: €{product['price']}")
                print(f"    Razão: {product['reasoning']}")
        else:
            print("  (nenhum produto)")
        
        # Verificar presença de pavimento e revestimento
        has_pavimento = any('pavimento' in p['name'].lower() for p in laje_products.values())
        has_revestimento = any('revestimento' in p['name'].lower() for p in laje_products.values())
        
        print(f"  Pavimento: {'✓' if has_pavimento else '✗'}")
        print(f"  Revestimento: {'✓' if has_revestimento else '✗'}")
        
        # Se era esperado revestimento mas não tem
        if answers.get('revestimento_laje') == 'sim' and not has_revestimento:
            material = answers.get('material_revestimento', '')
            print(f"  ⚠️ PROBLEMA: Material '{material}' pode não existir na lista!")
        
        print()
    
    # Mostrar lista completa de materiais disponíveis
    print("--- MATERIAIS DISPONÍVEIS ---")
    
    # Extrair da função (copiando do código)
    precos_revestimento = {
        'granito_vila_real': 35.0,
        'granito_pedras_salgadas': 35.0,
        'granito_preto_angola': 90.0,
        'granito_preto_zimbabue': 140.0,
        'marmore_branco_ibiza': 90.0,
        'travertino_turco': 90.0,
        'pedra_hijau': 40.0
    }
    
    nomes_materiais = {
        'granito_vila_real': 'Granito Vila Real',
        'granito_pedras_salgadas': 'Granito Pedras Salgadas',
        'granito_preto_angola': 'Granito Preto Angola',
        'granito_preto_zimbabue': 'Granito Preto Zimbabue',
        'marmore_branco_ibiza': 'Mármore Branco Ibiza',
        'travertino_turco': 'Travertino Turco',
        'pedra_hijau': 'Pedra Hijau'
    }
    
    print("Códigos de material válidos:")
    for codigo, nome in nomes_materiais.items():
        preco = precos_revestimento[codigo]
        print(f"  {codigo} → {nome} (€{preco}/m²)")
    
    print("\n🔍 DIAGNÓSTICO:")
    print("O problema é que 'travertino_navona' não existe na lista!")
    print("Deveria ser 'travertino_turco'")

if __name__ == "__main__":
    debug_laje_revestimento()
