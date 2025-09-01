#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def main():
    conn = sqlite3.connect('database/pool_budgets.db')
    cursor = conn.cursor()
    
    print("=== CATEGORIAS DA FAMÍLIA REVESTIMENTO ===")
    cursor.execute("""
        SELECT pc.id, pc.name 
        FROM product_categories pc
        JOIN product_families pf ON pc.family_id = pf.id
        WHERE pf.name = 'Revestimento'
        ORDER BY pc.display_order, pc.name
    """)
    
    for row in cursor.fetchall():
        print(f'ID: {row[0]} | {row[1]}')
    
    conn.close()

if __name__ == "__main__":
    main()
