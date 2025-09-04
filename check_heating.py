import sqlite3

# Conectar à base de dados
conn = sqlite3.connect('database/pool_budgets.db')
cursor = conn.cursor()

print('=== CATEGORIAS DA FAMÍLIA AQUECIMENTO ===')
cursor.execute('SELECT id, name FROM product_categories WHERE family_id = 5')
categories = cursor.fetchall()
for row in categories:
    print(f'ID: {row[0]} | Nome: {row[1]}')

print('\n=== PRODUTOS DA FAMÍLIA AQUECIMENTO ===')
cursor.execute('SELECT p.id, p.name, p.base_price, c.name as categoria FROM products p JOIN product_categories c ON p.category_id = c.id WHERE c.family_id = 5')
products = cursor.fetchall()
for row in products:
    print(f'ID: {row[0]} | Nome: {row[1]} | Preço: {row[2]} | Categoria: {row[3]}')

if not categories:
    print('Nenhuma categoria encontrada para família Aquecimento')
if not products:
    print('Nenhum produto encontrado para família Aquecimento')

conn.close()
