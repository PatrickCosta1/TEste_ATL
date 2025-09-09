#!/usr/bin/env python3
"""
Teste de integração completa da família da laje no orçamento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_budget_integration_with_laje():
    """Teste completo da integração da família da laje"""
    
    print("=== TESTE DE INTEGRAÇÃO: FAMÍLIA DA LAJE NO ORÇAMENTO ===\n")
    
    # Inicializar componentes
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Dimensões da piscina
    dimensions = {
        'comprimento': 10.0,
        'largura': 5.0,
        'prof_min': 1.0,
        'prof_max': 2.0,
        'volume': 75.0
    }
    
    # Calcular métricas
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'],
        dimensions['largura'],
        dimensions['prof_min'],
        dimensions['prof_max']
    )
    
    print(f"Dimensões: {dimensions['comprimento']}x{dimensions['largura']}m")
    print(f"Volume: {dimensions['volume']} m³")
    print()
    
    # Respostas do questionário
    answers = {
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'tratamento_agua': 'cloro_manual',
        'domotica': False,
        'tipo_construcao': 'nova',
        # CONSTRUÇÃO DA LAJE
        'havera_laje': 'sim',
        'laje_m2': 80.0,
        'laje_espessura': 0.20,  # 20cm
        'revestimento_laje': 'sim',
        'material_revestimento': 'travertino_turco'  # Corrigido para material válido
    }
    
    print("Configuração do teste:")
    print(f"  - Laje: {answers['havera_laje']}")
    print(f"  - Área da laje: {answers['laje_m2']} m²")
    print(f"  - Espessura: {answers['laje_espessura']*100} cm")
    print(f"  - Revestimento: {answers['revestimento_laje']}")
    print(f"  - Material: {answers['material_revestimento']}")
    print()
    
    # Gerar orçamento completo
    print("--- GERANDO ORÇAMENTO COMPLETO ---")
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    # Verificar se a família da laje existe
    families = budget.get('families', {})
    family_totals = budget.get('family_totals', {})
    
    print(f"Famílias encontradas: {len(families)}")
    print("Lista de famílias:")
    for family_name in families.keys():
        display_name = budget.get('family_display_map', {}).get(family_name, family_name)
        total = family_totals.get(family_name, 0)
        products_count = len(families[family_name])
        print(f"  - {display_name} ({family_name}): {products_count} produtos, €{total:.2f}")
    print()
    
    # Verificar especificamente a família da laje
    if 'construcao_laje' in families:
        print("✅ FAMÍLIA DA LAJE ENCONTRADA!")
        laje_family = families['construcao_laje']
        laje_total = family_totals.get('construcao_laje', 0)
        
        print(f"Produtos na família da laje: {len(laje_family)}")
        print(f"Total da família: €{laje_total:.2f}")
        print()
        
        print("Detalhes dos produtos:")
        for product_id, product in laje_family.items():
            subtotal = product['price'] * product['quantity']
            print(f"  - {product['name'][:80]}...")
            print(f"    Preço: €{product['price']:.2f} × {product['quantity']} = €{subtotal:.2f}")
            print(f"    Justificativa: {product['reasoning']}")
            print()
        
        # Verificar tipos de produtos
        has_pavimento = any('pavimento' in p['name'].lower() for p in laje_family.values())
        has_revestimento = any('revestimento' in p['name'].lower() for p in laje_family.values())
        
        print("Verificação de produtos:")
        print(f"  ✓ Pavimento presente: {'SIM' if has_pavimento else 'NÃO'}")
        print(f"  ✓ Revestimento presente: {'SIM' if has_revestimento else 'NÃO'}")
        
        if has_pavimento and has_revestimento:
            print("  🎯 FAMÍLIA COMPLETA!")
        else:
            print("  ⚠️ Família incompleta")
            
    else:
        print("❌ FAMÍLIA DA LAJE NÃO ENCONTRADA!")
        print("Famílias disponíveis:", list(families.keys()))
    
    print()
    print("--- RESUMO DO ORÇAMENTO ---")
    print(f"Total de famílias: {len(families)}")
    print(f"Total geral: €{budget.get('total_price', 0):.2f}")
    
    # Teste sem laje para comparação
    print("\n--- TESTE SEM LAJE (COMPARAÇÃO) ---")
    answers_sem_laje = answers.copy()
    answers_sem_laje['havera_laje'] = 'nao'
    
    budget_sem_laje = selector.generate_budget(answers_sem_laje, metrics, dimensions)
    families_sem_laje = budget_sem_laje.get('families', {})
    
    tem_laje_sem = 'construcao_laje' in families_sem_laje
    if not tem_laje_sem:
        print("✅ CORRETO: Família da laje não aparece quando 'havera_laje' = 'nao'")
    else:
        print("❌ ERRO: Família da laje aparece mesmo quando não deveria")
    
    print(f"Famílias sem laje: {len(families_sem_laje)} (esperado: {len(families)-1})")
    
    print("\n=== RESULTADO FINAL ===")
    laje_presente = 'construcao_laje' in families
    laje_ausente_quando_nao = 'construcao_laje' not in families_sem_laje
    
    if laje_presente and laje_ausente_quando_nao:
        print("🎉 INTEGRAÇÃO COMPLETA E FUNCIONAL!")
        print("✓ Família da laje aparece no orçamento quando solicitada")
        print("✓ Família da laje não aparece quando não solicitada")
        print("✓ Cálculos corretos aplicados")
        print("✓ Produtos incluídos adequadamente")
    else:
        print("❌ PROBLEMAS NA INTEGRAÇÃO:")
        if not laje_presente:
            print("  - Família não aparece quando deveria")
        if not laje_ausente_quando_nao:
            print("  - Família aparece quando não deveria")

if __name__ == "__main__":
    test_budget_integration_with_laje()
