#!/usr/bin/env python3
"""
Script para verificar se o heliaço está sendo adicionado aos orçamentos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_heliaco_logic():
    """Testa a lógica de adição do heliaço"""
    
    print("=== TESTE DA LÓGICA DO HELIAÇO ===\n")
    
    # Criar instâncias
    calculator = PoolCalculator()
    selector = AdvancedProductSelector()
    
    # Dados de teste - piscina básica
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.0
    }
    
    # Calcular métricas
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'],
        dimensions['largura'], 
        dimensions['prof_min'],
        dimensions['prof_max']
    )
    
    print(f"Dimensões da piscina:")
    print(f"  Comprimento: {dimensions['comprimento']} m")
    print(f"  Largura: {dimensions['largura']} m") 
    print(f"  Prof. min: {dimensions['prof_min']} m")
    print(f"  Prof. max: {dimensions['prof_max']} m")
    print()
    
    print(f"Métricas calculadas:")
    print(f"  Perímetro: {metrics.get('perimetro', 0):.2f} m")
    print(f"  M² paredes: {metrics.get('m2_paredes', 0):.2f} m²")
    print(f"  M³ massa: {metrics.get('m3_massa', 0):.2f} m³")
    print()
    
    # Respostas básicas do questionário
    answers = {
        'acesso': 'facil',
        'escavacao': 'mecanica',
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'vinil',
        'domotica': 'nao',
        'localizacao': 'exterior',
        'luz': 'led',
        'tratamento_agua': 'cloro_manual',
        'tipo_construcao': 'nova',
        'cobertura': 'nao',
        'localidade': 'Porto/Maia/Matosinhos'  # Para garantir preços conhecidos
    }
    
    print("Respostas do questionário:")
    for key, value in answers.items():
        print(f"  {key}: {value}")
    print()
    
    # Gerar orçamento
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    # Verificar se existe família construção
    construcao_family = budget.get('families', {}).get('construcao', {})
    
    print("=== ANÁLISE DA FAMÍLIA CONSTRUÇÃO ===")
    print(f"Família construção existe: {'SIM' if construcao_family else 'NÃO'}")
    print(f"Produtos na construção: {len(construcao_family)}")
    print()
    
    if construcao_family:
        print("Produtos encontrados na construção:")
        for product_key, product_data in construcao_family.items():
            name = product_data.get('name', 'Sem nome')
            quantity = product_data.get('quantity', 0)
            price = product_data.get('price', 0)
            reasoning = product_data.get('reasoning', 'Sem explicação')
            
            print(f"  {product_key}:")
            print(f"    Nome: {name}")
            print(f"    Quantidade: {quantity}")
            print(f"    Preço: {price:.2f} €")
            print(f"    Explicação: {reasoning}")
            print()
        
        # Verificar especificamente o heliaço
        heliaco_found = False
        for product_key, product_data in construcao_family.items():
            if 'heliaco' in product_key.lower() or 'heliaço' in product_data.get('name', '').lower():
                heliaco_found = True
                print("🎯 HELIAÇO ENCONTRADO!")
                print(f"  Chave: {product_key}")
                print(f"  Nome: {product_data.get('name')}")
                print(f"  Quantidade: {product_data.get('quantity')}")
                print(f"  Preço: {product_data.get('price', 0):.2f} €")
                print(f"  Explicação: {product_data.get('reasoning')}")
                break
        
        if not heliaco_found:
            print("❌ HELIAÇO NÃO ENCONTRADO!")
            print("Vamos verificar as condições para adição...")
            
            # Verificar condições manualmente
            perimetro = metrics.get('perimetro', 0)
            prof_max = dimensions.get('prof_max', 0)
            
            print(f"\nCondições para heliaço:")
            print(f"  perimetro > 0: {perimetro} > 0 = {perimetro > 0}")
            print(f"  prof_max > 0: {prof_max} > 0 = {prof_max > 0}")
            print(f"  Ambas verdadeiras: {perimetro > 0 and prof_max > 0}")
            
            if perimetro > 0 and prof_max > 0:
                # Calcular manualmente
                altura_2m = perimetro / 0.2
                barras_verticais = (altura_2m * 2) / 6
                n_fiadas = prof_max / 0.2
                barras_horizontais = (n_fiadas * perimetro * 2) / 6
                import math
                qty_heliaco = math.ceil(barras_verticais + barras_horizontais)
                
                print(f"\nCálculo manual do heliaço:")
                print(f"  Altura_2m = {perimetro}/0.2 = {altura_2m}")
                print(f"  Barras verticais = ({altura_2m} * 2)/6 = {barras_verticais:.2f}")
                print(f"  Nº fiadas = {prof_max}/0.2 = {n_fiadas}")
                print(f"  Barras horizontais = ({n_fiadas} * {perimetro} * 2)/6 = {barras_horizontais:.2f}")
                print(f"  Total barras = {barras_verticais:.2f} + {barras_horizontais:.2f} = {barras_verticais + barras_horizontais:.2f}")
                print(f"  Quantidade heliaço = ceil({barras_verticais + barras_horizontais:.2f}) = {qty_heliaco}")
                
                print(f"\n🤔 As condições estão corretas, mas o heliaço não foi adicionado!")
                print("Isso sugere um problema na implementação.")
            
    else:
        print("❌ FAMÍLIA CONSTRUÇÃO NÃO EXISTE!")
        print("Isso indica um problema maior na geração do orçamento.")
    
    print("\n=== RESUMO ===")
    total_families = len(budget.get('families', {}))
    print(f"Total de famílias no orçamento: {total_families}")
    
    for family_name, family_products in budget.get('families', {}).items():
        print(f"  {family_name}: {len(family_products)} produtos")

if __name__ == "__main__":
    test_heliaco_logic()
