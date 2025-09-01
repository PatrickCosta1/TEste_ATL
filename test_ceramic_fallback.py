#!/usr/bin/env python3
"""
Teste para verificar se os produtos de cerâmica são selecionados corretamente
usando o sistema de fallback (default_data.py)
"""

# Forçar uso do fallback
import os
os.environ['USE_FALLBACK'] = '1'

from advanced_product_selector import AdvancedProductSelector

def test_ceramic_fallback():
    print("=== TESTE COM FALLBACK (default_data.py) ===")
    
    selector = AdvancedProductSelector()
    
    # Dados de teste com revestimento cerâmico
    answers = {
        'piscina_tipo': 'enterrada',
        'revestimento': 'ceramica',  # Tipo de revestimento cerâmico
        'forma_piscina': 'standard',
        'tipo_construcao': 'nova',
        'acesso': 'facil',
        'escavacao': 'nao',
        'cobertura': 'nao'
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
    
    metrics = {
        'm2_paredes': 33.6,
        'm2_fundo': 32.0,
        'volume_total': 44.8
    }
    
    print(f"Testando com revestimento: {answers['revestimento']}")
    
    try:
        result = selector.generate_budget(answers, metrics, dimensions)
        
        if result and 'families' in result:
            revestimento_family = result['families'].get('Revestimento', {})
            
            if revestimento_family:
                print("\n✅ FAMÍLIA REVESTIMENTO ENCONTRADA!")
                for key, item in revestimento_family.items():
                    print(f"  • {item['name']}")
                    print(f"    Preço: €{item['price']}")
                    print(f"    Quantidade: {item['quantity']} {item['unit']}")
                    if item.get('editable_name'):
                        print(f"    ✓ Nome editável")
                    if item.get('editable_price'):
                        print(f"    ✓ Preço editável")
                    print()
            else:
                print("❌ Família Revestimento não foi criada")
                print("Famílias disponíveis:", list(result['families'].keys()))
        else:
            print("❌ Erro: resultado inválido")
            print("Resultado:", result)
    
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ceramic_fallback()
