#!/usr/bin/env python3
"""
Script de verificação completa da nova família "Construção da Laje"
Verifica integração com formulário, processamento e geração de orçamentos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator
import json

def test_integration():
    """Testa integração completa da família construção da laje"""
    
    print("=== VERIFICAÇÃO COMPLETA: CONSTRUÇÃO DA LAJE ===\n")
    
    # Inicializar componentes
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Simular dados vindos do formulário (como em app.py)
    form_data = {
        'comprimento': '8',
        'largura': '4',
        'prof_min': '1.0',
        'prof_max': '2.0',
        'acesso': 'facil',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': '60',
        'laje_espessura': '0.18',  # 18cm em metros
        'revestimento_laje': 'sim',
        'material_revestimento': 'granito_preto_angola'
    }
    
    print("Dados do formulário:")
    for key, value in form_data.items():
        if 'laje' in key or key in ['comprimento', 'largura']:
            print(f"  {key}: {value}")
    print()
    
    # Simular processamento como em app.py
    try:
        dimensions = {
            'comprimento': float(form_data['comprimento']),
            'largura': float(form_data['largura']),
            'prof_min': float(form_data['prof_min']),
            'prof_max': float(form_data['prof_max'])
        }
        
        # Calcular métricas
        metrics = calculator.calculate_all_metrics(
            dimensions['comprimento'],
            dimensions['largura'],
            dimensions['prof_min'],
            dimensions['prof_max']
        )
        
        # Processar respostas (como em app.py)
        answers = {
            'acesso': form_data.get('acesso'),
            'forma': form_data.get('forma'),
            'tipo_piscina': form_data.get('tipo_piscina'),
            'revestimento': form_data.get('revestimento'),
            'localizacao': form_data.get('localizacao'),
            'luz': form_data.get('luz'),
            'havera_laje': form_data.get('havera_laje'),
            'laje_m2': float(form_data.get('laje_m2', 0)) if form_data.get('laje_m2') else 0,
            'laje_espessura': float(form_data.get('laje_espessura', 0)) if form_data.get('laje_espessura') else 0,
            'revestimento_laje': form_data.get('revestimento_laje'),
            'material_revestimento': form_data.get('material_revestimento')
        }
        
        print("Respostas processadas:")
        for key, value in answers.items():
            if 'laje' in key:
                print(f"  {key}: {value}")
        print()
        
        # Gerar orçamento completo
        budget = selector.generate_budget(answers, metrics, dimensions)
        
        if budget and 'families' in budget:
            print("Famílias no orçamento:")
            for family_name, products in budget['families'].items():
                print(f"  - {family_name}: {len(products)} produtos")
            print()
            
            # Verificar família de construção da laje
            laje_family = budget['families'].get('construcao_laje', {})
            
            if laje_family:
                print("✓ Família 'Construção da Laje' encontrada no orçamento")
                print(f"Produtos da família: {len(laje_family)}")
                
                total_laje = 0
                for product_id, product in laje_family.items():
                    subtotal = product['price'] * product['quantity']
                    total_laje += subtotal
                    print(f"  - {product['name'][:80]}...")
                    print(f"    Preço: €{product['price']} × {product['quantity']} = €{subtotal}")
                    print(f"    Cálculo: {product.get('reasoning', 'N/A')}")
                    print()
                
                print(f"Total da família Construção da Laje: €{total_laje:.2f}")
                
                # Verificar se tem pavimento e revestimento
                has_pavimento = any('pavimento' in p['name'].lower() for p in laje_family.values())
                has_revestimento = any('revestimento' in p['name'].lower() for p in laje_family.values())
                
                if has_pavimento:
                    print("✓ Produto de pavimento presente")
                if has_revestimento:
                    print("✓ Produto de revestimento presente")
                
                if has_pavimento and has_revestimento:
                    print("✓ INTEGRAÇÃO COMPLETA FUNCIONAL")
                elif has_pavimento:
                    print("✓ Integração parcial funcional (apenas pavimento)")
                else:
                    print("❌ Integração com problemas")
                    
            else:
                print("❌ Família 'Construção da Laje' não encontrada no orçamento")
                
        else:
            print("❌ Erro ao gerar orçamento")
            
        print(f"\nTotal do orçamento: €{budget.get('total_price', 0)}")
        
    except Exception as e:
        print(f"❌ Erro durante teste de integração: {str(e)}")
        import traceback
        traceback.print_exc()

def test_display_mapping():
    """Verifica se o mapeamento de exibição está correto"""
    
    print("\n=== VERIFICAÇÃO: MAPEAMENTO DE EXIBIÇÃO ===")
    
    selector = AdvancedProductSelector()
    
    # Verificar se a família está no mapeamento
    if hasattr(selector, 'family_display_names'):
        display_names = selector.family_display_names
        if 'construcao_laje' in display_names:
            print(f"✓ Família mapeada: construcao_laje → {display_names['construcao_laje']}")
        else:
            print("❌ Família 'construcao_laje' não está mapeada para exibição")
    else:
        print("❌ Atributo family_display_names não encontrado")

if __name__ == "__main__":
    test_integration()
    test_display_mapping()
    print("\n=== VERIFICAÇÃO COMPLETA ===")
    