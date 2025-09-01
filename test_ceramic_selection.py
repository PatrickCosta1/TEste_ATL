#!/usr/bin/env python3

from database_manager import DatabaseManager

db = DatabaseManager()
conditions = {'coating_type': 'ceramico'}
products = db.get_products_by_conditions(conditions)
print(f'Produtos encontrados para coating_type=ceramico: {len(products)}')
for p in products:
    print(f'  {p["id"]} | {p["name"]} | {p["family_name"]}')
