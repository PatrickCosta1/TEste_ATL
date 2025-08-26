from database_manager import DatabaseManager

def main():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Primeiro, verificar qual é a família de recirculação
    print('=== FAMÍLIAS DISPONÍVEIS ===')
    cursor.execute('SELECT id, name FROM product_families ORDER BY name')
    families = cursor.fetchall()
    for family in families:
        print(f'ID: {family["id"]}, Nome: {family["name"]}')

    # Encontrar a família de recirculação (provavelmente "Recirculação e Iluminação - Encastráveis Tanque Piscina")
    cursor.execute('''
        SELECT id, name FROM product_families 
        WHERE name LIKE '%recircula%' OR name LIKE '%Recircula%'
    ''')
    recirculacao_family = cursor.fetchone()
    
    if not recirculacao_family:
        print('\n❌ Família de recirculação não encontrada!')
        return
    
    family_id = recirculacao_family['id']
    family_name = recirculacao_family['name']
    
    print(f'\n=== PRODUTOS DA FAMÍLIA: {family_name} ===')
    
    # Verificar produtos da família recirculação e suas alternativas
    cursor.execute('''
        SELECT p.id, p.name, pc.name as category_name, p.can_change_type 
        FROM products p 
        JOIN product_categories pc ON p.category_id = pc.id
        WHERE pc.family_id = ? AND p.is_active = 1
        ORDER BY pc.name, p.name
    ''', (family_id,))
    
    recirculacao_products = cursor.fetchall()
    for product in recirculacao_products:
        print(f'ID: {product["id"]}, Nome: {product["name"]}, Categoria: {product["category_name"]}, Can_Change: {product["can_change_type"]}')

    print('\n=== VERIFICANDO ALTERNATIVAS PARA CADA PRODUTO ===')
    for product in recirculacao_products:
        product_id = product['id']
        name = product['name']
        category_name = product['category_name']
        can_change = product['can_change_type']
        
        if can_change:
            # Buscar outras alternativas na mesma categoria
            cursor.execute('''
                SELECT p2.id, p2.name 
                FROM products p2 
                JOIN product_categories pc ON p2.category_id = pc.id
                WHERE pc.name = ? AND pc.family_id = ? AND p2.id != ? AND p2.is_active = 1
                ORDER BY p2.name
            ''', (category_name, family_id, product_id))
            alternatives = cursor.fetchall()
            
            print(f'\n{name} (ID: {product_id}, Categoria: {category_name}):')
            if alternatives:
                for alt in alternatives:
                    print(f'  - Alternativa: {alt["name"]} (ID: {alt["id"]})')
            else:
                print(f'  - SEM ALTERNATIVAS ENCONTRADAS')
        else:
            print(f'\n{name} (ID: {product_id}, Categoria: {category_name}): NÃO PERMITE TROCA')

    # Verificar também se há produtos com can_change_type = 0
    print('\n=== PRODUTOS QUE NÃO PERMITEM TROCA ===')
    cursor.execute('''
        SELECT p.id, p.name, pc.name as category_name 
        FROM products p 
        JOIN product_categories pc ON p.category_id = pc.id
        WHERE pc.family_id = ? AND p.can_change_type = 0 AND p.is_active = 1
        ORDER BY pc.name, p.name
    ''', (family_id,))
    
    no_change_products = cursor.fetchall()
    for product in no_change_products:
        print(f'ID: {product["id"]}, Nome: {product["name"]}, Categoria: {product["category_name"]}')

    conn.close()

if __name__ == "__main__":
    main()
