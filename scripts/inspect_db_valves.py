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
# procurar categorias com 'valv' (ignora acentos)
c.execute("SELECT id, name FROM product_categories WHERE lower(name) LIKE '%valv%' OR lower(name) LIKE '%válv%'")
rows = c.fetchall()
print('Categories found:', len(rows))
for r in rows:
    print(dict(r))
    cid = r['id']
    c2 = conn.cursor()
    c2.execute('SELECT id, name, base_price FROM products WHERE category_id = ? AND is_active = 1', (cid,))
    prods = c2.fetchall()
    print('Active products in category:', len(prods))
    for p in prods:
        print(' -', p['id'], p['name'], p['base_price'])

# Also list products whose name contains 'válvula' or 'valvula'
c.execute("SELECT id, name, base_price, category_id FROM products WHERE lower(name) LIKE '%valvula%' OR lower(name) LIKE '%válvula%'")
prods = c.fetchall()
print('\nProducts with valvula in name:', len(prods))
for p in prods:
    print(dict(p))

conn.close()
