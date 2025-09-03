#!/usr/bin/env python3
"""
Script completo para testar cerâmica no modo local e fallback
"""

import os
from advanced_product_selector import AdvancedProductSelector

def test_both_modes():
    print("=== TESTE MODO NORMAL (BD) ===")
    test_ceramic_mode("normal")
    
    print("\n" + "="*50)
    print("=== TESTE MODO FALLBACK ===")
    
    # Simular ausência da base de dados
    os.environ['USE_FALLBACK'] = '1'
    test_ceramic_mode("fallback")

def test_ceramic_mode(mode):
    selector = AdvancedProductSelector()
    
    answers = {
        'revestimento': 'ceramica',
        'forma_piscina': 'standard',
        'tipo_construcao': 'nova',
        'acesso': 'facil',
        'escavacao': 'nao',
        'cobertura': 'nao'
    }
    
    metrics = {
        'm2_paredes': 30.0,
        'm2_fundo': 25.0,
    }
    
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 1.8,
        'prof_media': 1.4,
        'volume': 44.8,
        'area_superficie': 32.0
    }
    
    try:
        result = selector.generate_budget(answers, metrics, dimensions)
        
        if result and 'families' in result:
            if 'revestimento' in result['families']:
                revestimento_family = result['families']['revestimento']
                print(f"✅ {mode.upper()}: Família revestimento encontrada! ({len(revestimento_family)} produtos)")
                
                for key, item in revestimento_family.items():
                    print(f"  • {item['name'][:60]}...")
                    print(f"    ID: {item.get('product_id', 'N/A')}")
                    print(f"    Quantidade: {item['quantity']} {item['unit']}")
                    print(f"    Preço: €{item['price']}")
                    features = []
                    if item.get('editable_price'):
                        features.append("preço editável")
                    if item.get('editable_cost'):
                        features.append("custo editável")
                    if item.get('editable_name'):
                        features.append("nome editável")
                    if features:
                        print(f"    Recursos: {', '.join(features)}")
                    print()
            else:
                print(f"❌ {mode.upper()}: Família revestimento não encontrada")
                print(f"Famílias disponíveis: {list(result['families'].keys())}")
        else:
            print(f"❌ {mode.upper()}: Resultado inválido")
    
    except Exception as e:
        print(f"❌ {mode.upper()}: Erro - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_both_modes()
