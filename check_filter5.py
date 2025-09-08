import urllib.request
import json

def check_session_alternatives():
    try:
        with urllib.request.urlopen('http://localhost:5000/get_session_data') as response:
            session_data = json.loads(response.read().decode())
            
        budget = session_data.get('current_budget', {})
        families = budget.get('families', {})
        
        print("=== VERIFICAÇÃO DE PRODUTOS ALTERNATIVOS NA SESSÃO ===")
        
        found_filter_5 = False
        for family_name, family_products in families.items():
            alternatives_in_family = []
            
            for product_key, product_data in family_products.items():
                item_type = product_data.get('item_type', 'incluido')
                
                if item_type == 'alternativo':
                    name = product_data.get('name', 'Sem nome')
                    quantity = product_data.get('quantity', 0)
                    alternative_to = product_data.get('alternative_to', 'N/A')
                    
                    alternatives_in_family.append({
                        'key': product_key,
                        'name': name,
                        'quantity': quantity,
                        'alternative_to': alternative_to
                    })
                    
                    if product_key == 'filter_5':
                        found_filter_5 = True
                        print(f"✅ FILTER_5 ENCONTRADO!")
                        print(f"   Key: {product_key}")
                        print(f"   Name: {name}")
                        print(f"   Quantity: {quantity}")
                        print(f"   Alternative to: {alternative_to}")
                        print(f"   Item type: {item_type}")
            
            if alternatives_in_family:
                print(f"\n{family_name.upper()}:")
                for alt in alternatives_in_family:
                    marker = "🔍" if alt['key'] == 'filter_5' else "○"
                    print(f"  {marker} {alt['key']}: {alt['name']} (Qty: {alt['quantity']}, Alt to: {alt['alternative_to']})")
        
        if not found_filter_5:
            print("\n❌ FILTER_5 NÃO ENCONTRADO NA SESSÃO!")
            
            # Listar todas as chaves da família filtracao para debug
            filtracao = families.get('filtracao', {})
            print(f"\nChaves na família 'filtracao': {list(filtracao.keys())}")
        else:
            print(f"\n✅ filter_5 está corretamente na sessão")
            
    except Exception as e:
        print(f"Erro ao verificar sessão: {e}")

if __name__ == "__main__":
    check_session_alternatives()
