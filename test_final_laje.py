#!/usr/bin/env python3
"""
Teste final para verificar se a família da laje aparece no frontend
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_complete_workflow():
    """Simula o workflow completo e verifica estrutura final"""
    
    print("=== TESTE FINAL: ESTRUTURA DO ORÇAMENTO ===\n")
    
    # Inicializar
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Dados de teste
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.0
    }
    
    answers = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 40.0,
        'laje_espessura': 0.15,
        'revestimento_laje': 'sim',
        'material_revestimento': 'granito_vila_real'
    }
    
    # Calcular métricas
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'],
        dimensions['largura'],
        dimensions['prof_min'],
        dimensions['prof_max']
    )
    
    # Gerar orçamento
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    if budget and 'families' in budget:
        print("ESTRUTURA DO ORÇAMENTO FINAL:")
        print("=" * 50)
        
        # Verificar a ordem das famílias como aparecerão no template
        family_order = ['filtracao', 'recirculacao_iluminacao', 'tratamento_agua', 'revestimento', 'aquecimento', 'construcao', 'construcao_laje']
        
        for i, family_name in enumerate(family_order, 1):
            if family_name in budget['families']:
                family_products = budget['families'][family_name]
                family_total = budget.get('family_totals_base', {}).get(family_name, 0)
                
                # Mapear nomes para exibição
                family_display_names = {
                    'filtracao': 'Filtração',
                    'recirculacao_iluminacao': 'Recirculação e Iluminação',
                    'tratamento_agua': 'Tratamento de Água',
                    'revestimento': 'Revestimento',
                    'aquecimento': 'Aquecimento',
                    'construcao': 'Construção da Piscina',
                    'construcao_laje': 'Construção da Laje'
                }
                
                display_name = family_display_names.get(family_name, family_name.title())
                
                print(f"{i}. {display_name}")
                print(f"   Chave: {family_name}")
                print(f"   Produtos: {len(family_products)}")
                print(f"   Total: €{family_total:.2f}")
                
                # Se for a família da laje, mostrar detalhes
                if family_name == 'construcao_laje':
                    print("   DETALHES DOS PRODUTOS:")
                    for product_id, product in family_products.items():
                        print(f"     - {product['name'][:60]}...")
                        print(f"       Preço: €{product['price']} × {product['quantity']}")
                
                print()
        
        # Verificar se família da laje está presente
        if 'construcao_laje' in budget['families']:
            laje_products = budget['families']['construcao_laje']
            if len(laje_products) > 0:
                print("✅ SUCESSO: Família 'Construção da Laje' está presente e será exibida")
                print(f"   Produtos na família: {len(laje_products)}")
                print(f"   Total da família: €{budget.get('family_totals_base', {}).get('construcao_laje', 0):.2f}")
            else:
                print("❌ ERRO: Família 'Construção da Laje' existe mas sem produtos")
        else:
            print("❌ ERRO: Família 'Construção da Laje' não encontrada no orçamento")
    
    else:
        print("❌ ERRO: Falha ao gerar orçamento")

if __name__ == "__main__":
    test_complete_workflow()
