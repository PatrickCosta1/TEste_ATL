#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from advanced_product_selector import AdvancedProductSelector
from database_manager import DatabaseManager

def test_ceramic_coating():
    selector = AdvancedProductSelector()
    
    # Simular métricas calculadas
    metrics = {
        'ml_bordadura': 24.0,        # 2*(8+4) = 24m de bordadura
        'm2_paredes': 42.0,          # 2*(8+4)*1.75 = 42 m²
        'm2_fundo': 32.0,            # Calculado com fórmula específica
        'area_total': 74.0           # 42+32 = 74 m²
    }
    
    # Simular dimensões da piscina
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.5,
        'prof_media': 1.75,
        'volume': 56.0,
        'm3_h': 28.0
    }
    
    answers = {
        'revestimento': 'ceramico',  # Tipo de revestimento cerâmico
        'forma_piscina': 'standard',
        'tipo_construcao': 'nova',
        'acesso': 'facil',
        'escavacao': 'nao',
        'cobertura': 'nao'
    }
    
    print("=== TESTE REVESTIMENTO CERÂMICO ===")
    print(f"Piscina: {dimensions['comprimento']}x{dimensions['largura']}m")
    print(f"Profundidade média: {dimensions['prof_media']}m")
    print(f"Tipo de revestimento: {answers['revestimento']}")
    
    # Executar seleção de produtos
    result = selector.generate_budget(answers, metrics, dimensions)
    
    if result and 'revestimento' in result:
        print("\n=== PRODUTOS DE REVESTIMENTO SELECIONADOS ===")
        revestimento_items = result['revestimento']
        
        for key, item in revestimento_items.items():
            print(f"\nItem: {key}")
            print(f"  Nome: {item['name']}")
            print(f"  Preço: €{item['price']}")
            print(f"  Quantidade: {item['quantity']} {item['unit']}")
            print(f"  Tipo: {item['item_type']}")
            print(f"  Motivo: {item['reasoning']}")
            if item.get('editable_name'):
                print(f"  ✅ Nome editável")
            if item.get('editable_price'):
                print(f"  ✅ Preço editável")
            if item.get('editable_cost'):
                print(f"  ✅ Custo editável")
    elif result and 'families' in result:
        print("\n=== FAMÍLIAS NO RESULTADO ===")
        families = result['families']
        for family_name, family_items in families.items():
            print(f"\nFamília: {family_name}")
            if family_items:
                for key, item in family_items.items():
                    print(f"  Item: {key}")
                    print(f"    Nome: {item['name']}")
                    print(f"    Preço: €{item['price']}")
                    print(f"    Quantidade: {item['quantity']} {item['unit']}")
                    if item.get('editable_name'):
                        print(f"    ✅ Nome editável")
                    if item.get('editable_price'):
                        print(f"    ✅ Preço editável")
            else:
                print(f"  (sem itens)")
    else:
        print("❌ Nenhum produto de revestimento foi selecionado")
        print("Resultado completo:", result.keys() if result else "None")

if __name__ == "__main__":
    test_ceramic_coating()
