import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pool_budgets.db')
print('DB path:', DB)
print('Exists:', os.path.exists(DB))
if not os.path.exists(DB):
    raise SystemExit('DB not found')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
# listar produtos na categoria 3 (Válvulas Seletoras)
cat_id = 3
c.execute('SELECT id, name, base_price, is_active FROM products WHERE category_id = ? ORDER BY id', (cat_id,))
rows = c.fetchall()
print('Products in category id=3:', len(rows))
for r in rows:
    print(dict(r))

# listar todos os produtos com 'válv' no nome
c.execute("SELECT id, name, base_price, category_id, is_active FROM products WHERE lower(name) LIKE '%valv%' ORDER BY id")
rows = c.fetchall()
print('\nProducts with valv in name:', len(rows))
for r in rows:
    print(dict(r))

conn.close()
