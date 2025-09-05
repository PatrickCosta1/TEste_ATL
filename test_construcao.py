#!/usr/bin/env python3
# Script de teste para debug da família Construção da Piscina

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

def test_construcao():
    # Criar instância do seletor
    selector = AdvancedProductSelector()
    calc = PoolCalculator()
    
    # Dados de teste
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.0
    }
    
    # Garantir que prof_min e prof_max estão presentes e possuem valores válidos
    if 'prof_min' not in dimensions or 'prof_max' not in dimensions or dimensions['prof_min'] is None or dimensions['prof_max'] is None:
        raise ValueError("Os parâmetros 'prof_min' e 'prof_max' são obrigatórios e devem ter valores em 'dimensions'.")

    answers = {
        'acesso': 'facil',
        'escavacao': False,
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'tela',
        'domotica': False,
        'localizacao': 'exterior',
        'luz': 'monofasica',
        'zona_praia': 'sim',
        'zona_praia_largura': 2.0,
        'zona_praia_comprimento': 4.0,
        'escadas': 'sim',
        'escadas_largura': 1.0,
        'localidade': 'Viseu'
    }
    
    # Calcular métricas
    metrics = calc.calculate_all_metrics(
        dimensions['comprimento'], 
        dimensions['largura'], 
        dimensions['prof_min'], 
        dimensions['prof_max']
    )
    print(f"Métricas calculadas: {metrics}")
    
    # Definir condições
    conditions = {
        'location': answers.get('localizacao', 'exterior'),
        'domotics': str(answers.get('domotica', False)).lower(),
        'pool_type': answers.get('tipo_piscina', 'skimmer'),
        'coating_type': answers.get('revestimento', 'tela'),
        'power_type': answers.get('luz', 'monofasica'),
        'casa_maquinas_abaixo': answers.get('casa_maquinas_abaixo', 'nao'),
        'tipo_luzes': answers.get('tipo_luzes', 'branco_frio'),
        'tratamento_agua': answers.get('tratamento_agua', 'nao')
    }
    
    # Testar função diretamente
    print("\n=== Testando função _select_construction_products ===")
    try:
        construcao = selector._select_construction_products(conditions, dimensions, metrics, answers)
        print(f"Produtos de construção: {len(construcao)} itens")
        
        for key, item in construcao.items():
            print(f"- {key}: {item['name']} | Qty: {item['quantity']} {item['unit']} | €{item['price']:.2f}")
            
        return construcao
    except Exception as e:
        print(f"ERRO na função _select_construction_products: {e}")
        import traceback
        traceback.print_exc()
        return {}

def test_full_budget():
    print("\n=== Testando generate_budget completo ===")
    selector = AdvancedProductSelector()
    calc = PoolCalculator()
    
    dimensions = {
        'comprimento': 8.0,
        'largura': 4.0,
        'prof_min': 1.0,
        'prof_max': 2.0
    }
    
    answers = {
        'acesso': 'facil',
        'escavacao': False,
        'forma': 'retangular',
        'tipo_piscina': 'skimmer',
        'revestimento': 'tela',
        'domotica': False,
        'localizacao': 'exterior',
        'luz': 'monofasica',
        'zona_praia': 'sim',
        'zona_praia_largura': 2.0,
        'zona_praia_comprimento': 4.0,
        'escadas': 'sim',
        'escadas_largura': 1.0,
        'localidade': 'Viseu'
    }
    
    metrics = calc.calculate_all_metrics(
        dimensions,
        answers,
        prof_min=dimensions.get('prof_min'),
        prof_max=dimensions.get('prof_max')
    )
    
    try:
        budget = selector.generate_budget(answers, metrics, dimensions)
        print(f"Famílias no orçamento: {list(budget['families'].keys())}")
        
        if 'construcao' in budget['families']:
            construcao = budget['families']['construcao']
            print(f"Família Construção: {len(construcao)} produtos")
            for key, item in construcao.items():
                print(f"- {item['name']}: {item['quantity']} {item['unit']} @ €{item['price']}")
        else:
            print("❌ Família 'construcao' não encontrada no orçamento!")
            
    except Exception as e:
        print(f"ERRO no generate_budget: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 Teste da Família Construção da Piscina")
    print("=" * 50)
    
    # Teste 1: Função direta
    construcao_direct = test_construcao()
    
    # Teste 2: Budget completo
    test_full_budget()
