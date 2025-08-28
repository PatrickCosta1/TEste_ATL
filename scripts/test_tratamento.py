#!/usr/bin/env python3
"""
Script para testar a lógica de tratamento de água
"""

from advanced_product_selector import AdvancedProductSelector
from database_manager import DatabaseManager

def test_tratamento():
    selector = AdvancedProductSelector()
    db = DatabaseManager()
    
    # Simular dados de teste
    answers = {
        'tratamento_agua': 'clorador_salino',
        'comprimento': 8,
        'largura': 4,
        'prof_min': 1.2,
        'prof_max': 1.8
    }
    
    metrics = {
        'volume': 50,
        'm3_h': 15
    }
    
    dimensions = {
        'volume': 50
    }
    
    print("=== TESTE DE TRATAMENTO DE ÁGUA ===")
    print(f"Resposta tratamento_agua: {answers.get('tratamento_agua')}")
    print(f"Volume: {dimensions.get('volume')} m³")
    print(f"m3/h: {metrics.get('m3_h')}")
    
    # Verificar se produtos existem na base
    print("\n=== PRODUTOS DISPONÍVEIS ===")
    produtos = db.get_products_by_family('Tratamento de Água')
    for p in produtos:
        print(f"- {p['name']} (€{p['base_price']})")
    
    # Testar lógica
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    print("\n=== FAMÍLIA TRATAMENTO ÁGUA NO ORÇAMENTO ===")
    tratamento = budget.get('families', {}).get('tratamento_agua', {})
    
    if tratamento:
        for key, item in tratamento.items():
            print(f"- {item['name']}: €{item['price']} x {item['quantity']} = €{item['price'] * item['quantity']}")
    else:
        print("❌ Nenhum produto de tratamento encontrado!")

if __name__ == "__main__":
    test_tratamento()
