#!/usr/bin/env python3
"""
Teste detalhado da lógica de seleção de produtos cerâmicos
"""

from advanced_product_selector import AdvancedProductSelector

def debug_ceramic_logic():
    print("=== DEBUG LÓGICA CERÂMICA ===")
    
    selector = AdvancedProductSelector()
    
    # Simular exatamente as condições que seriam passadas
    answers = {
        'revestimento': 'ceramica',  # Valor do questionário
    }
    
    metrics = {
        'm2_paredes': 30.0,
        'm2_fundo': 25.0,
    }
    
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
    }
    
    # Testar diretamente a função _select_revestimento_products
    print("Testando _select_revestimento_products diretamente...")
    
    # Criar as condições como o generate_budget faria
    conditions = {
        'coating_type': answers.get('revestimento', 'tela')  # Deve ser 'ceramica'
    }
    
    print(f"Condições criadas: {conditions}")
    
    try:
        # Testar o generate_budget completo com debug
        print("Chamando generate_budget...")
        full_result = selector.generate_budget(answers, metrics, dimensions)
        
        if full_result and 'families' in full_result:
            print("Famílias no resultado:")
            for family_name in full_result['families'].keys():
                print(f"  • {family_name}")
                
            if 'revestimento' in full_result['families']:
                print("\n✅ Família revestimento encontrada!")
                revestimento_family = full_result['families']['revestimento']
                for key, item in revestimento_family.items():
                    print(f"  • {item['name']}")
                    print(f"    Quantidade: {item['quantity']} {item['unit']}")
                    print(f"    Preço: €{item['price']}")
                    if item.get('editable_price'):
                        print(f"    ✓ Preço editável")
                    if item.get('editable_name'):
                        print(f"    ✓ Nome editável")
            else:
                print("❌ Família revestimento não encontrada")
        else:
            print("❌ Resultado inválido ou vazio")
            print("Resultado completo:", full_result)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ceramic_logic()
