#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

def main():
    db_path = "database/pool_budgets.db"
    
    if not os.path.exists(db_path):
        print(f"Database não encontrada: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== FAMÍLIA REVESTIMENTO ===")
    
    # Listar produtos da família Revestimento
    cursor.execute("""
        SELECT p.id, p.name, p.base_price, pc.name as category_name, pf.name as family_name
        FROM products p
        JOIN product_categories pc ON p.category_id = pc.id
        JOIN product_families pf ON pc.family_id = pf.id
        WHERE pf.name = 'Revestimento' AND p.is_active = 1
        ORDER BY pc.name, p.name
    """)
    
    products = cursor.fetchall()
    
    current_category = None
    for product in products:
        if product['category_name'] != current_category:
            current_category = product['category_name']
            print(f"\n--- {current_category} ---")
        
        print(f"ID: {product['id']} | {product['name']} | €{product['base_price']}")
    
    print(f"\nTotal de produtos: {len(products)}")
    
    conn.close()

if __name__ == "__main__":
    main()
