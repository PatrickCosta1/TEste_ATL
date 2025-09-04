#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se os produtos de aquecimento Mr. Comfort 
estão sendo selecionados corretamente baseado no volume da piscina.
"""

from advanced_product_selector import AdvancedProductSelector

def test_heating_selection():
    """Testa a seleção de produtos de aquecimento por volume"""
    
    selector = AdvancedProductSelector()
    
    # Cenários de teste com diferentes volumes
    test_cases = [
        {'volume': 25, 'expected_model': '90M', 'description': 'Piscina pequena'},
        {'volume': 45, 'expected_model': '130M', 'description': 'Piscina média-pequena'},
        {'volume': 65, 'expected_model': '160M', 'description': 'Piscina média'},
        {'volume': 80, 'expected_model': '200M', 'description': 'Piscina média-grande'},
        {'volume': 100, 'expected_model': '240M', 'description': 'Piscina grande'},
        {'volume': 150, 'expected_model': '240M', 'description': 'Piscina muito grande'},
    ]
    
    print("=== TESTE DE SELEÇÃO DE AQUECIMENTO MR. COMFORT ===\n")
    
    for case in test_cases:
        volume = case['volume']
        expected = case['expected_model']
        description = case['description']
        
        print(f"🔍 Testando {description} (Volume: {volume} m³)")
        
        # Dados de teste
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
        
        metrics = {
            'volume': volume,
            'm3_h': 8
        }
        
        dimensions = {
            'volume': volume,
            'comprimento': 8,
            'largura': 4,
            'profundidade': 1.5
        }
        
        try:
            # Gerar orçamento
            budget = selector.generate_budget(answers, metrics, dimensions)
            
            # Verificar se família aquecimento existe
            if 'aquecimento' in budget['families']:
                aquecimento_items = budget['families']['aquecimento']
                
                if aquecimento_items:
                    for key, item in aquecimento_items.items():
                        if 'Mr. Comfort' in item['name']:
                            print(f"   ✅ Selecionado: {item['name']}")
                            print(f"   💰 Preço: €{item['price']}")
                            print(f"   📝 Razão: {item['reasoning']}")
                            
                            # Verificar se o modelo corresponde ao esperado
                            if expected in item['name']:
                                print(f"   ✅ CORRETO: Modelo {expected} selecionado conforme esperado")
                            else:
                                print(f"   ❌ ERRO: Esperado modelo {expected}, mas foi selecionado {item['name']}")
                            break
                    else:
                        print(f"   ❌ ERRO: Nenhum produto Mr. Comfort encontrado")
                else:
                    print(f"   ⚠️  Nenhum produto de aquecimento selecionado")
            else:
                print(f"   ❌ ERRO: Família 'aquecimento' não encontrada no orçamento")
                print(f"   📋 Famílias disponíveis: {list(budget['families'].keys())}")
        
        except Exception as e:
            print(f"   ❌ ERRO durante geração do orçamento: {e}")
        
        print()

    print("=== TESTE FINALIZADO ===")

if __name__ == "__main__":
    test_heating_selection()
