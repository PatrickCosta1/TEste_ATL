#!/usr/bin/env python3
"""
Teste específico para debug dos problemas reportados:
1. Campo de domótica vazio no modal
2. Erro ao alternar entre item incluído e alternativo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import json

def test_domotica_field():
    """Testa se o campo de domótica está sendo passado corretamente"""
    print("=== TESTE: CAMPO DE DOMÓTICA ===\n")
    
    with app.test_client() as client:
        # Simular dados de uma sessão com domótica ativa
        with client.session_transaction() as sess:
            sess['current_budget'] = {
                'pool_info': {
                    'answers': {
                        'domotica': True,  # Python boolean
                        'tipo_piscina': 'skimmer',
                        'revestimento': 'vinil',
                        'localizacao': 'exterior'
                    }
                },
                'families': {
                    'filtracao': {
                        'filter_1': {
                            'name': 'Filtro Teste',
                            'price': 100,
                            'quantity': 1,
                            'item_type': 'incluido'
                        }
                    }
                }
            }
        
        # Fazer request para a página de orçamento
        response = client.get('/budget')
        
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            
            # Verificar se domótica está sendo passada corretamente
            if '"true"' in content and 'domotica' in content:
                print("✅ Campo domótica encontrado no HTML")
                
                # Procurar o valor específico
                import re
                domotica_pattern = r"domotica:\s*'([^']*)"
                matches = re.findall(domotica_pattern, content)
                
                if matches:
                    print(f"Valor encontrado: '{matches[0]}'")
                    if matches[0] == 'true':
                        print("✅ Valor correto (true)")
                    else:
                        print(f"❌ Valor incorreto: esperado 'true', encontrado '{matches[0]}'")
                else:
                    print("❌ Padrão de domótica não encontrado")
            else:
                print("❌ Campo domótica não encontrado no HTML")
        else:
            print(f"❌ Erro na resposta: {response.status_code}")

def test_replace_product_api():
    """Testa o endpoint de substituição de produtos"""
    print("\n=== TESTE: ENDPOINT REPLACE PRODUCT ===\n")
    
    with app.test_client() as client:
        # Simular dados de uma sessão
        with client.session_transaction() as sess:
            sess['current_budget'] = {
                'families': {
                    'filtracao': {
                        'filter_1': {
                            'id': '1',
                            'name': 'Filtro Original',
                            'price': 100,
                            'quantity': 1,
                            'item_type': 'incluido',
                            'unit': 'un'
                        }
                    }
                },
                'family_totals': {
                    'filtracao': 100
                },
                'total_price': 100
            }
        
        # Testar substituição de produto
        replace_data = {
            'family': 'filtracao',
            'current_product_id': 'filter_1',
            'new_product_id': '2'  # ID de um produto alternativo
        }
        
        response = client.post('/replace_product', 
                             data=json.dumps(replace_data),
                             content_type='application/json')
        
        if response.status_code == 200:
            result = response.get_json()
            print(f"Status da resposta: {response.status_code}")
            print(f"Resposta: {result}")
            
            if result.get('success'):
                print("✅ Substituição bem-sucedida")
            else:
                print(f"❌ Erro na substituição: {result.get('error')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"Resposta: {response.data.decode('utf-8')}")

def test_boolean_conversion():
    """Testa conversão de valores booleanos"""
    print("\n=== TESTE: CONVERSÃO DE BOOLEANOS ===\n")
    
    # Simular como os valores são processados no template
    test_values = [True, False, 'true', 'false', None, '']
    
    for value in test_values:
        # Simulação da lógica do template Jinja2
        converted = "true" if value else "false"
        print(f"Valor original: {value} ({type(value)}) → Convertido: '{converted}'")

if __name__ == "__main__":
    test_boolean_conversion()
    test_domotica_field()
    test_replace_product_api()
