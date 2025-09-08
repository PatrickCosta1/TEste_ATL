import urllib.request
import json

try:
    with urllib.request.urlopen('http://localhost:5000/debug_totals') as response:
        data = json.loads(response.read().decode())
        
    print("=== VERIFICAÇÃO DE PRODUTOS ALTERNATIVOS ===")
    
    # Verificar se há produtos alternativos nos dados
    found_alternatives = False
    
    if 'produtos_incluidos' in data:
        produtos = data['produtos_incluidos']
        print(f"Total de produtos incluídos: {len(produtos)}")
        for prod in produtos:
            print(f"  ✓ {prod['family']}: {prod['name']}")
    
    print("\n=== VERIFICAR DADOS COMPLETOS DA SESSÃO ===")
    # Tentar obter dados completos da sessão
    try:
        with urllib.request.urlopen('http://localhost:5000/get_session_data') as response:
            session_data = json.loads(response.read().decode())
            
        budget = session_data.get('current_budget', {})
        families = budget.get('families', {})
        
        print("Famílias no orçamento:")
        for family_name, family_products in families.items():
            print(f"\n{family_name.upper()}:")
            for product_key, product_data in family_products.items():
                item_type = product_data.get('item_type', 'incluido')
                name = product_data.get('name', 'Sem nome')
                quantity = product_data.get('quantity', 0)
                
                if item_type == 'alternativo':
                    alternative_to = product_data.get('alternative_to', 'N/A')
                    print(f"  ○ ALT: {name} (Qty: {quantity}, Alt to: {alternative_to})")
                    found_alternatives = True
                else:
                    status = "✓" if item_type == 'incluido' else "◯"
                    print(f"  {status} {item_type.upper()}: {name} (Qty: {quantity})")
        
        if not found_alternatives:
            print("\n❌ NENHUM PRODUTO ALTERNATIVO ENCONTRADO NA SESSÃO!")
        else:
            print("\n✅ Produtos alternativos encontrados na sessão")
            
    except Exception as e:
        print(f"Erro ao obter dados da sessão: {e}")
        
except Exception as e:
    print(f"Erro: {e}")
