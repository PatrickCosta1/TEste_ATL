#!/usr/bin/env python3
"""
Script para verificar estrutura das tabelas
"""

import sqlite3

# Conectar à base de dados
conn = sqlite3.connect('database/pool_budgets.db')
cursor = conn.cursor()

print("🔍 ESTRUTURA DAS TABELAS")
print("=" * 40)

# Verificar tabela product_attributes
cursor.execute("PRAGMA table_info(product_attributes)")
columns = cursor.fetchall()

print("📋 Tabela: product_attributes")
for col in columns:
    print(f"  • {col[1]} ({col[2]}) - Nulo: {col[3]} - Default: {col[4]}")

# Verificar estrutura de outras tabelas relacionadas
tables = ['attribute_types', 'products', 'product_families', 'product_categories']

for table in tables:
    print(f"\n📋 Tabela: {table}")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  • {col[1]} ({col[2]})")

conn.close()
