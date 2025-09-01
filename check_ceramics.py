#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('database/pool_budgets.db')
cursor = conn.cursor()

print('=== PRODUTOS DE CERÂMICA ===')
cursor.execute('SELECT id, name FROM products WHERE id IN (102, 103)')
for row in cursor.fetchall():
    print(f'ID: {row[0]} | Nome: {row[1]}')

print('\n=== CATEGORIA CERÂMICA ===')
cursor.execute('SELECT id, name, family_id FROM product_categories WHERE name = "Cerâmica"')
for row in cursor.fetchall():
    print(f'ID: {row[0]} | Nome: {row[1]} | Família: {row[2]}')

print('\n=== REGRAS DE SELEÇÃO PARA CERÂMICA ===')
cursor.execute('SELECT id, product_id, condition_type, condition_value FROM selection_rules WHERE product_id IN (102, 103)')
for row in cursor.fetchall():
    print(f'Regra: {row[0]} | Produto: {row[1]} | Tipo: {row[2]} | Valor: {row[3]}')

conn.close()
