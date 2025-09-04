from database_manager import DatabaseManager

def main():
    db = DatabaseManager()
    
    # Testar alguns produtos da família recirculação
    print('=== TESTANDO ALTERNATIVAS PARA PRODUTOS DE RECIRCULAÇÃO ===')
    
    # Buscar produtos da família recirculação
    family_name = 'Recirculação e Iluminação'
    products = db.get_products_by_family(family_name)
    
    print(f'Total de produtos encontrados na família "{family_name}": {len(products)}')
    
    # Agrupar por categoria
    categories = {}
    for product in products:
        category = product.get('category_name', 'Sem Categoria')
        if category not in categories:
            categories[category] = []
        categories[category].append(product)
    
    print(f'\n=== PRODUTOS POR CATEGORIA ===')
    for category, prods in categories.items():
        print(f'\n📂 {category} ({len(prods)} produtos):')
        for prod in prods:
            print(f'  - {prod["name"]} (ID: {prod["id"]})')
        
        # Se houver mais de um produto, há alternativas
        if len(prods) > 1:
            print(f'  ✅ Esta categoria tem {len(prods)-1} alternativas por produto')
        else:
            print(f'  ❌ Esta categoria não tem alternativas')
    
    # Testar especificamente um produto
    print(f'\n=== TESTANDO PRODUTO ESPECÍFICO ===')
    if products:
        test_product = products[0]  # Pegar o primeiro produto
        print(f'Produto de teste: {test_product["name"]} (ID: {test_product["id"]})')
        
        # Buscar alternativas
        current_category = test_product.get('category_name', '')
        same_category_products = [p for p in products if p.get('category_name', '') == current_category]
        
        print(f'Produtos na mesma categoria "{current_category}":')
        for p in same_category_products:
            if p['id'] != test_product['id']:
                print(f'  - Alternativa: {p["name"]} (ID: {p["id"]})')
        
        if len(same_category_products) <= 1:
            print('  - SEM ALTERNATIVAS ENCONTRADAS')

if __name__ == "__main__":
    main()
