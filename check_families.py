import sqlite3

# Conectar à base de dados
conn = sqlite3.connect('database/pool_budgets.db')
cursor = conn.cursor()

print('=== FAMÍLIAS EXISTENTES ===')
cursor.execute('SELECT id, name FROM product_families ORDER BY id')
for row in cursor.fetchall():
    print(f'ID: {row[0]} | Nome: {row[1]}')

print('\n=== VERIFICAR AQUECIMENTO ===')
cursor.execute("SELECT id, name FROM product_families WHERE name LIKE '%aquecimento%' OR name LIKE '%Aquecimento%'")
result = cursor.fetchall()
if result:
    for row in result:
        print(f'ID: {row[0]} | Nome: {row[1]}')
else:
    print('Família Aquecimento não encontrada')

conn.close()
