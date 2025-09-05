#!/usr/bin/env python3
# Teste de debug para verificar porque a família construção não aparece na web

from advanced_product_selector import AdvancedProductSelector
from calculator import PoolCalculator

# Simular os dados exatos que vêm do frontend
data_from_form = {
    'comprimento': '8',
    'largura': '4', 
    'prof_min': '1',
    'prof_max': '2',
    'acesso': 'facil',
    'escavacao': 'false',
    'forma': 'retangular',
    'tipo_piscina': 'skimmer',
    'revestimento': 'tela',
    'domotica': 'false',
    'localizacao': 'exterior',
    'luz': 'monofasica',
    'zona_praia': 'sim',
    'zona_praia_largura': '2',
    'zona_praia_comprimento': '4',
    'escadas': 'sim',
    'escadas_largura': '1',
    'localidade': 'Viseu'  # ESTE CAMPO PODE ESTAR FALTANDO NO FORM
}

print("🔧 Debug Frontend vs Backend")
print("=" * 50)

# Simular processamento do app.py
answers = {
    'acesso': data_from_form.get('acesso'),
    'escavacao': str(data_from_form.get('escavacao', 'false')).lower() == 'true',
    'forma': data_from_form.get('forma'),
    'tipo_piscina': data_from_form.get('tipo_piscina'),
    'revestimento': data_from_form.get('revestimento'),
    'domotica': str(data_from_form.get('domotica', 'false')).lower() == 'true',
    'localizacao': data_from_form.get('localizacao'),
    'luz': data_from_form.get('luz'),
    'zona_praia': data_from_form.get('zona_praia'),
    'zona_praia_largura': float(data_from_form.get('zona_praia_largura', 0)) if data_from_form.get('zona_praia_largura') else 0,
    'zona_praia_comprimento': float(data_from_form.get('zona_praia_comprimento', 0)) if data_from_form.get('zona_praia_comprimento') else 0,
    'escadas': data_from_form.get('escadas'),
    'escadas_largura': float(data_from_form.get('escadas_largura', 0)) if data_from_form.get('escadas_largura') else 0,
    'localidade': data_from_form.get('localidade')  # IMPORTANTE!
}

dimensions = {
    'comprimento': float(data_from_form.get('comprimento', 0)),
    'largura': float(data_from_form.get('largura', 0)),
    'prof_min': float(data_from_form.get('prof_min', 0)),
    'prof_max': float(data_from_form.get('prof_max', 0))
}

print(f"✓ Answers processadas: {answers}")
print(f"✓ Localidade nos answers: {answers.get('localidade', 'FALTANDO!')}")

# Calcular métricas
calc = PoolCalculator()
metrics = calc.calculate_all_metrics(
    dimensions['comprimento'], 
    dimensions['largura'], 
    dimensions['prof_min'], 
    dimensions['prof_max']
)

print(f"✓ Métricas: {metrics}")

# Gerar orçamento
selector = AdvancedProductSelector()
budget = selector.generate_budget(answers, metrics, dimensions)

print(f"✓ Famílias no orçamento: {list(budget['families'].keys())}")

if 'construcao' in budget['families']:
    construcao = budget['families']['construcao']
    print(f"✅ Família Construção encontrada: {len(construcao)} produtos")
    total = 0
    for key, item in construcao.items():
        price = item['price'] * item['quantity']
        total += price
        print(f"  - {item['name']}: {item['quantity']} @ €{item['price']}")
    print(f"✅ Total: €{total:.2f}")
else:
    print("❌ Família Construção NÃO encontrada!")
    print("   Verificando possíveis problemas...")
    
    # Testar condições diretas
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
    
    try:
        construcao_direto = selector._select_construction_products(conditions, dimensions, metrics, answers)
        print(f"   Teste direto da função: {len(construcao_direto)} produtos")
        if construcao_direto:
            print("   Função funciona diretamente! Problema na integração.")
        else:
            print("   Função não retorna produtos. Verificar lógica interna.")
    except Exception as e:
        print(f"   ERRO na função: {e}")
