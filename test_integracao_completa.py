#!/usr/bin/env python3
"""
Teste de integração completa - verificar se a família da laje aparece no orçamento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_budget_integration_with_laje():
    """Testa integração completa incluindo a família da laje"""
    
    print("=== TESTE INTEGRAÇÃO COMPLETA: FAMÍLIA DA LAJE ===\n")
    
    # Inicializar componentes
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Simular dados completos
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.0,
        'volume': 48.0
    }
    
    # Calcular métricas
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'],
        dimensions['largura'],
        dimensions['prof_min'],
        dimensions['prof_max']
    )
    
    # Respostas completas COM laje
    answers = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'tratamento_agua': 'cloro_manual',
        'domotica': False,
        'aquecimento': 'nao',
        # LAJE
        'havera_laje': 'sim',
        'laje_m2': 50.0,
        'laje_espessura': 0.15,
        'revestimento_laje': 'sim',
        'material_revestimento': 'travertino_turco'
    }
    
    print("--- TESTE: Geração de orçamento completo ---")
    
    # Gerar orçamento completo
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    print(f"Famílias encontradas: {list(budget.get('families', {}).keys())}")
    print(f"Totais por família: {budget.get('family_totals', {})}")
    print()
    
    # Verificar se a família da laje está presente
    families = budget.get('families', {})
    family_totals = budget.get('family_totals', {})
    
    if 'construcao_laje' in families:
        print("✅ Família 'construcao_laje' ENCONTRADA nas families")
        laje_products = families['construcao_laje']
        print(f"   Produtos na família: {len(laje_products)}")
        
        for product_id, product in laje_products.items():
            if product['quantity'] > 0:
                subtotal = product['price'] * product['quantity']
                print(f"   - {product['name'][:50]}...")
                print(f"     Qtd: {product['quantity']} | Preço: €{product['price']} | Subtotal: €{subtotal}")
        
        if 'construcao_laje' in family_totals:
            print(f"✅ Total da família: €{family_totals['construcao_laje']}")
        else:
            print("❌ Total da família NÃO encontrado")
            
    else:
        print("❌ Família 'construcao_laje' NÃO ENCONTRADA")
        print("   Verificando se produtos foram gerados...")
        
        # Testar diretamente a função
        laje_products = selector._select_laje_products(answers, dimensions)
        print(f"   Produtos diretos da função: {len(laje_products)}")
        
        if len(laje_products) > 0:
            print("   ⚠️  Função gera produtos, mas não aparecem no budget!")
        else:
            print("   ❌ Função não gera produtos")
    
    print()
    
    # Verificar display mapping
    display_map = budget.get('family_display_map', {})
    if 'construcao_laje' in display_map:
        print(f"✅ Display mapping: construcao_laje -> '{display_map['construcao_laje']}'")
    else:
        print("❌ Display mapping para 'construcao_laje' não encontrado")
    
    print()
    
    # Teste SEM laje para comparação
    print("--- TESTE: Sem laje para comparação ---")
    answers_sem_laje = answers.copy()
    answers_sem_laje['havera_laje'] = 'nao'
    
    budget_sem_laje = selector.generate_budget(answers_sem_laje, metrics, dimensions)
    families_sem_laje = budget_sem_laje.get('families', {})
    
    if 'construcao_laje' in families_sem_laje:
        laje_empty = families_sem_laje['construcao_laje']
        if len(laje_empty) == 0:
            print("✅ Sem laje: família vazia corretamente")
        else:
            print(f"❌ Sem laje: família tem {len(laje_empty)} produtos (deveria estar vazia)")
    else:
        print("✅ Sem laje: família não presente (correto)")
    
    print("\n=== RESUMO FINAL ===")
    
    has_family = 'construcao_laje' in families
    has_products = has_family and len(families.get('construcao_laje', {})) > 0
    has_total = 'construcao_laje' in family_totals
    has_display = 'construcao_laje' in display_map
    
    print(f"✓ Família presente no budget: {'SIM' if has_family else 'NÃO'}")
    print(f"✓ Produtos na família: {'SIM' if has_products else 'NÃO'}")
    print(f"✓ Total calculado: {'SIM' if has_total else 'NÃO'}")
    print(f"✓ Display mapping: {'SIM' if has_display else 'NÃO'}")
    
    if all([has_family, has_products, has_total, has_display]):
        print("\n🎉 INTEGRAÇÃO COMPLETA: SUCESSO!")
        print("A família da laje deve aparecer no orçamento web.")
    else:
        print("\n❌ PROBLEMAS NA INTEGRAÇÃO")
        print("A família pode não aparecer corretamente no orçamento web.")
    
    return budget

if __name__ == "__main__":
    test_budget_integration_with_laje()
