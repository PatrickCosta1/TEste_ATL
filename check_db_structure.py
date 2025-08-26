from database_manager import DatabaseManager

def main():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Verificar estrutura da tabela products
    print('=== ESTRUTURA DA TABELA PRODUCTS ===')
    cursor.execute('PRAGMA table_info(products)')
    columns = cursor.fetchall()
    print('Colunas da tabela products:')
    for col in columns:
        print(f'- {col[1]} ({col[2]})')

    # Verificar se existe algum campo relacionado a alternativas
    print('\n=== BUSCAR CAMPOS RELACIONADOS A ALTERNATIVAS ===')
    column_names = [col[1] for col in columns]
    alternative_fields = [col for col in column_names if 'change' in col.lower() or 'alternative' in col.lower() or 'switch' in col.lower()]
    if alternative_fields:
        print(f'Campos relacionados a alternativas: {alternative_fields}')
    else:
        print('Nenhum campo específico para alternativas encontrado')

    # Verificar alguns produtos da família recirculação
    print('\n=== PRODUTOS DA FAMÍLIA RECIRCULAÇÃO (AMOSTRA) ===')
    cursor.execute('''
        SELECT p.id, p.name, pc.name as category_name
        FROM products p 
        JOIN product_categories pc ON p.category_id = pc.id
        WHERE pc.family_id = 2 AND p.is_active = 1
        ORDER BY pc.name, p.name
        LIMIT 10
    ''')
    
    products = cursor.fetchall()
    for product in products:
        print(f'ID: {product["id"]}, Nome: {product["name"]}, Categoria: {product["category_name"]}')

    conn.close()

if __name__ == "__main__":
    main()
