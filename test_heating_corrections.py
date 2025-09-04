#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste rápido para verificar as correções:
1. Ordem das famílias
2. Preço não editável nos produtos de aquecimento
"""

from advanced_product_selector import AdvancedProductSelector

def test_heating_corrections():
    """Testa as correções aplicadas"""
    
    selector = AdvancedProductSelector()
    
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
        'volume': 50,  # Volume que deve selecionar Mr. Comfort 130M
        'm3_h': 8
    }
    
    dimensions = {
        'volume': 50,
        'comprimento': 8,
        'largura': 4,
        'profundidade': 1.5
    }
    
    print("=== TESTE DAS CORREÇÕES ===\n")
    
    try:
        # Gerar orçamento
        budget = selector.generate_budget(answers, metrics, dimensions)
        
        # 1. Verificar ordem das famílias
        print("1. ORDEM DAS FAMÍLIAS:")
        families_list = list(budget['families'].keys())
        expected_order = ['filtracao', 'recirculacao_iluminacao', 'tratamento_agua', 'revestimento', 'aquecimento']
        
        print(f"   Ordem atual: {families_list}")
        print(f"   Ordem esperada: {expected_order}")
        
        if families_list == expected_order:
            print("   ✅ Ordem das famílias está CORRETA")
        else:
            print("   ❌ Ordem das famílias está INCORRETA")
        
        # 2. Verificar se aquecimento não está editável
        print("\n2. PREÇO EDITÁVEL DO AQUECIMENTO:")
        if 'aquecimento' in budget['families']:
            aquecimento_items = budget['families']['aquecimento']
            
            for key, item in aquecimento_items.items():
                if 'Mr. Comfort' in item['name']:
                    editable_price = item.get('editable_price', True)
                    print(f"   Produto: {item['name']}")
                    print(f"   Preço editável: {editable_price}")
                    
                    if editable_price == False:
                        print("   ✅ Preço NÃO editável está CORRETO")
                    else:
                        print("   ❌ Preço ainda está editável - INCORRETO")
                    break
            else:
                print("   ❌ Nenhum produto Mr. Comfort encontrado")
        else:
            print("   ❌ Família aquecimento não encontrada")
        
        # 3. Verificar item_type
        print("\n3. TIPO DO ITEM (incluido vs opcional):")
        if 'aquecimento' in budget['families']:
            aquecimento_items = budget['families']['aquecimento']
            
            for key, item in aquecimento_items.items():
                if 'Mr. Comfort' in item['name']:
                    item_type = item.get('item_type', 'opcional')
                    print(f"   Produto: {item['name']}")
                    print(f"   Tipo do item: {item_type}")
                    
                    if item_type == 'incluido':
                        print("   ✅ Item tipo 'incluido' está CORRETO")
                    else:
                        print("   ❌ Item ainda está como 'opcional' - INCORRETO")
                    break
    
    except Exception as e:
        print(f"❌ ERRO durante teste: {e}")
    
    print("\n=== TESTE FINALIZADO ===")

if __name__ == "__main__":
    test_heating_corrections()
