#!/usr/bin/env python3
"""
Debug específico para verificar por que os totais da família laje não aparecem
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def debug_family_totals():
    """Debug detalhado dos totais das famílias"""
    
    print("=== DEBUG: TOTAIS DAS FAMÍLIAS ===\n")
    
    # Inicializar
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Dados básicos
    dimensions = {'comprimento': 6.0, 'largura': 3.0, 'prof_min': 1.0, 'prof_max': 1.5}
    answers = {
        'acesso': 'facil',
        'forma': 'retangular', 
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'localizacao': 'exterior',
        'luz': 'led',
        'havera_laje': 'sim',
        'laje_m2': 25.0,
        'laje_espessura': 0.12,
        'revestimento_laje': 'nao'  # Só pavimento para simplificar
    }
    
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'], dimensions['largura'], 
        dimensions['prof_min'], dimensions['prof_max']
    )
    
    print("Métricas calculadas:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print()
    
    # Gerar orçamento
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    print("ANÁLISE DETALHADA DO ORÇAMENTO:")
    print("=" * 50)
    
    if budget and 'families' in budget:
        for family_name, family_products in budget['families'].items():
            print(f"\nFAMÍLIA: {family_name}")
            print(f"Produtos: {len(family_products)}")
            
            # Calcular total manualmente
            manual_total = 0
            for product_id, product in family_products.items():
                quantity = product.get('quantity', 0)
                price = product.get('price', 0)
                item_type = product.get('item_type', 'incluido')
                
                if quantity > 0 and item_type in ['incluido', 'opcional']:
                    subtotal = price * quantity
                    manual_total += subtotal
                    print(f"  ✓ {product['name'][:50]}...")
                    print(f"    Preço: €{price} × {quantity} = €{subtotal}")
                else:
                    print(f"  ○ {product['name'][:50]}... (ignorado: qty={quantity}, type={item_type})")
            
            print(f"Total manual calculado: €{manual_total}")
            print(f"Total do budget: €{budget.get('family_totals', {}).get(family_name, 'N/A')}")
            
            # Verificar se família específica da laje
            if family_name == 'construcao_laje':
                print("*** ESTA É A FAMÍLIA DA LAJE ***")
                if manual_total > 0:
                    print("✅ Família da laje tem valor > 0")
                else:
                    print("❌ Família da laje tem valor 0")
    
    print(f"\nTOTAL GERAL DO ORÇAMENTO: €{budget.get('total_price', 'N/A')}")

if __name__ == "__main__":
    debug_family_totals()
