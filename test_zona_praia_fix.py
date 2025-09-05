#!/usr/bin/env python3
"""
Teste para verificar se a correção da zona de praia está funcionando.
O comprimento da zona de praia deve ser sempre igual à largura da piscina.
"""

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_zona_praia_comprimento():
    print("=== TESTE: Comprimento da zona de praia = largura da piscina ===")
    
    # Dados de teste
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,  # Esta será usada como comprimento da zona de praia
        'prof_min': 1.0,
        'prof_max': 2.0,
        'volume': 48.0
    }
    
    answers = {
        'localizacao': 'exterior',
        'forma_piscina': 'standard',
        'tipo_piscina': 'skimmer',
        'revestimento': 'tela',
        'luz': 'monofasica',
        'domotica': False,
        'casa_maquinas_abaixo': 'nao',
        'tipo_luzes': 'branco_frio',
        'tratamento_agua': 'nao',
        'localidade': 'Porto/Maia/Matosinhos',
        
        # Zona de praia com largura mas SEM comprimento explícito
        'zona_praia': 'sim',
        'zona_praia_largura': 1.5,
        # 'zona_praia_comprimento' não está definido - deve usar largura da piscina (4.0)
        
        'escadas': 'nao'
    }
    
    # Calcular métricas
    calculator = PoolCalculator()
    metrics = calculator.calculate_all_metrics(
        dimensions['comprimento'], 
        dimensions['largura'], 
        dimensions['prof_min'], 
        dimensions['prof_max']
    )
    
    print(f"Dimensões da piscina: {dimensions['comprimento']}m × {dimensions['largura']}m")
    print(f"Zona de praia: largura = {answers['zona_praia_largura']}m")
    print(f"Comprimento da zona de praia esperado: {dimensions['largura']}m (= largura da piscina)")
    
    # Gerar orçamento
    selector = AdvancedProductSelector()
    budget = selector.generate_budget(answers, metrics, dimensions)
    
    # Verificar família de construção
    construcao = budget.get('families', {}).get('construcao', {})
    
    if not construcao:
        print("❌ ERRO: Família de construção não encontrada!")
        return False
    
    print(f"\n🔍 Produtos da família construção encontrados: {len(construcao)}")
    
    # Procurar por produtos relacionados com zona de praia (vigas e abobadilhas)
    vigas_found = None
    abobadilhas_found = None
    
    for key, product in construcao.items():
        if 'viga' in product['name'].lower():
            vigas_found = product
            print(f"✅ Vigas encontradas: {product['name']}")
            print(f"   Quantidade: {product['quantity']}")
            print(f"   Reasoning: {product['reasoning']}")
            
        if 'abobadilhas' in product['name'].lower():
            abobadilhas_found = product
            print(f"✅ Abobadilhas encontradas: {product['name']}")
            print(f"   Quantidade: {product['quantity']}")
            print(f"   Reasoning: {product['reasoning']}")
    
    # Verificar se os cálculos estão corretos
    largura_piscina = dimensions['largura']
    zona_praia_largura = answers['zona_praia_largura']
    
    print(f"\n📊 Verificação dos cálculos:")
    print(f"   Largura da piscina: {largura_piscina}m")
    print(f"   Largura da zona de praia: {zona_praia_largura}m")
    print(f"   Comprimento da zona de praia (automático): {largura_piscina}m")
    
    if vigas_found:
        # Cálculo esperado: ((comprimento_zona_praia / 0.52) + 1) × largura_zona_praia
        # comprimento_zona_praia = largura_piscina = 4.0
        expected_n_vigas = ((largura_piscina / 0.52) + 1) * zona_praia_largura
        actual_n_vigas = vigas_found['quantity']
        
        print(f"   Cálculo esperado de vigas: (({largura_piscina}/0.52)+1) × {zona_praia_largura} = {expected_n_vigas:.2f}")
        print(f"   Quantidade atual de vigas: {actual_n_vigas}")
        
        if abs(actual_n_vigas - expected_n_vigas) < 0.01:
            print("✅ Cálculo das vigas está correto!")
            return True
        else:
            print(f"❌ Cálculo das vigas está incorreto! Esperado: {expected_n_vigas:.2f}, Atual: {actual_n_vigas}")
            return False
    else:
        print("❌ Vigas não encontradas (esperado quando há zona de praia)")
        return False

if __name__ == "__main__":
    success = test_zona_praia_comprimento()
    print(f"\n{'='*50}")
    if success:
        print("✅ TESTE PASSOU: Comprimento da zona de praia = largura da piscina")
    else:
        print("❌ TESTE FALHOU: Verificar implementação")
    print(f"{'='*50}")
