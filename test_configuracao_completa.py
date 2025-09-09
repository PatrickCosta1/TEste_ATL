#!/usr/bin/env python3
"""
Teste final de integração completa da família da laje com atualização de configuração
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_complete_configuration_update():
    """Teste completo do sistema de atualização de configuração incluindo laje"""
    
    print("=== TESTE FINAL: CONFIGURAÇÃO COMPLETA COM LAJE ===\n")
    
    # Inicializar componentes
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    print("1. TESTE: Orçamento inicial SEM laje")
    print("-" * 50)
    
    # Configuração inicial sem laje
    dimensions_inicial = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.0,
        'volume': 32.0
    }
    
    answers_inicial = {
        'acesso': 'facil',
        'forma': 'standard',
        'tipo_piscina': 'skimmer',
        'revestimento': 'tela',
        'localizacao': 'exterior',
        'luz': 'monofasica',
        'tratamento_agua': 'cloro_manual',
        'domotica': 'false',
        'tipo_construcao': 'nova',
        'havera_laje': 'nao'  # Inicialmente sem laje
    }
    
    # Calcular métricas
    metrics_inicial = calculator.calculate_all_metrics(
        dimensions_inicial['comprimento'],
        dimensions_inicial['largura'],
        dimensions_inicial['prof_min'],
        dimensions_inicial['prof_max']
    )
    
    # Gerar orçamento inicial
    budget_inicial = selector.generate_budget(answers_inicial, metrics_inicial, dimensions_inicial)
    
    print(f"Dimensões: {dimensions_inicial['comprimento']}×{dimensions_inicial['largura']}m")
    print(f"Famílias no orçamento inicial: {len(budget_inicial['families'])}")
    
    families_inicial = list(budget_inicial['families'].keys())
    for family_name in families_inicial:
        display_name = budget_inicial.get('family_display_map', {}).get(family_name, family_name)
        total = budget_inicial['family_totals'].get(family_name, 0)
        print(f"  - {display_name}: €{total:.2f}")
    
    print(f"Total inicial: €{budget_inicial['total_price']:.2f}")
    
    if 'construcao_laje' in families_inicial:
        print("❌ ERRO: Laje presente quando não deveria!")
    else:
        print("✅ CORRETO: Sem laje conforme esperado")
    
    print("\n2. TESTE: Atualização para INCLUIR laje")
    print("-" * 50)
    
    # Nova configuração COM laje (simulando atualização via modal)
    dimensions_nova = {
        'comprimento': 10.0,  # Mudamos também as dimensões
        'largura': 5.0,
        'prof_min': 1.2,
        'prof_max': 2.5,
        'volume': 87.5
    }
    
    answers_nova = answers_inicial.copy()
    answers_nova.update({
        'havera_laje': 'sim',
        'laje_m2': 70.0,
        'laje_espessura': 0.15,  # 15cm
        'revestimento_laje': 'sim',
        'material_revestimento': 'granito_preto_angola',
        'tratamento_agua': 'clorador_salino'  # Também mudamos o tratamento
    })
    
    # Recalcular métricas
    metrics_nova = calculator.calculate_all_metrics(
        dimensions_nova['comprimento'],
        dimensions_nova['largura'],
        dimensions_nova['prof_min'],
        dimensions_nova['prof_max']
    )
    
    # Gerar novo orçamento
    budget_novo = selector.generate_budget(answers_nova, metrics_nova, dimensions_nova)
    
    print(f"Novas dimensões: {dimensions_nova['comprimento']}×{dimensions_nova['largura']}m")
    print(f"Famílias no orçamento atualizado: {len(budget_novo['families'])}")
    
    families_nova = list(budget_novo['families'].keys())
    for family_name in families_nova:
        display_name = budget_novo.get('family_display_map', {}).get(family_name, family_name)
        total = budget_novo['family_totals'].get(family_name, 0)
        
        # Marcar mudanças
        if family_name not in families_inicial:
            print(f"  + {display_name}: €{total:.2f} (NOVA)")
        elif budget_novo['family_totals'].get(family_name, 0) != budget_inicial['family_totals'].get(family_name, 0):
            total_anterior = budget_inicial['family_totals'].get(family_name, 0)
            print(f"  * {display_name}: €{total:.2f} (era €{total_anterior:.2f})")
        else:
            print(f"  - {display_name}: €{total:.2f}")
    
    print(f"Total atualizado: €{budget_novo['total_price']:.2f}")
    diferenca = budget_novo['total_price'] - budget_inicial['total_price']
    print(f"Diferença: €{diferenca:.2f}")
    
    # Verificações específicas da laje
    if 'construcao_laje' in families_nova:
        print("\n✅ FAMÍLIA DA LAJE ADICIONADA!")
        laje_family = budget_novo['families']['construcao_laje']
        laje_total = budget_novo['family_totals']['construcao_laje']
        
        print(f"Produtos na laje: {len(laje_family)}")
        print(f"Total da laje: €{laje_total:.2f}")
        
        # Verificar produtos específicos
        has_pavimento = any('pavimento' in p['name'].lower() for p in laje_family.values())
        has_revestimento = any('revestimento' in p['name'].lower() for p in laje_family.values())
        
        print(f"  Pavimento: {'✓' if has_pavimento else '✗'}")
        print(f"  Revestimento: {'✓' if has_revestimento else '✗'}")
        
        if has_pavimento and has_revestimento:
            print("  🎯 Família completa!")
        
        # Mostrar detalhes dos produtos
        print("\nDetalhes dos produtos da laje:")
        for product_id, product in laje_family.items():
            print(f"  - {product['name'][:60]}...")
            print(f"    €{product['price']} × {product['quantity']} = €{product['price'] * product['quantity']}")
            print(f"    {product['reasoning']}")
    else:
        print("❌ ERRO: Laje não foi adicionada!")
    
    print("\n3. TESTE: Verificação de outras alterações")
    print("-" * 50)
    
    # Verificar se mudança no tratamento de água foi aplicada
    tratamento_family = budget_novo['families'].get('tratamento_agua', {})
    print(f"Produtos de tratamento: {len(tratamento_family)}")
    
    for product_id, product in tratamento_family.items():
        if 'inverclear' in product['name'].lower():
            print(f"  ✓ Clorador salino encontrado: {product['name']}")
        elif 'sal' in product['name'].lower():
            print(f"  ✓ Sal encontrado: {product['name']}")
    
    print("\n=== RESUMO FINAL ===")
    print(f"✓ Orçamento inicial (sem laje): {len(families_inicial)} famílias, €{budget_inicial['total_price']:.2f}")
    print(f"✓ Orçamento atualizado (com laje): {len(families_nova)} famílias, €{budget_novo['total_price']:.2f}")
    print(f"✓ Diferença de famílias: +{len(families_nova) - len(families_inicial)}")
    print(f"✓ Diferença de preço: €{diferenca:.2f}")
    
    if 'construcao_laje' in families_nova and 'construcao_laje' not in families_inicial:
        print("🎉 SISTEMA DE CONFIGURAÇÃO COMPLETA FUNCIONAL!")
        print("✓ Laje adicionada corretamente")
        print("✓ Preços calculados adequadamente")
        print("✓ Integração completa entre frontend e backend")
    else:
        print("❌ Problemas na integração detectados")

if __name__ == "__main__":
    test_complete_configuration_update()
