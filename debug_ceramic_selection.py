#!/usr/bin/env python3
"""
Debug específico para entender por que a família revestimento não aparece com cerâmica
"""

from database_manager import DatabaseManager

def debug_ceramic_selection():
    print("=== DEBUG SELEÇÃO CERÂMICA ===")
    
    db = DatabaseManager()
    
    # Testar condições diretamente
    conditions = {'coating_type': 'ceramica'}
    
    print(f"Condições de busca: {conditions}")
    
    products = db.get_products_by_conditions(conditions)
    print(f"\nProdutos encontrados para coating_type=ceramica: {len(products)}")
    
    for p in products:
        print(f"  • ID: {p['id']} | {p['name'][:50]}...")
        print(f"    Família: {p.get('family_name', 'N/A')}")
        print(f"    Categoria: {p.get('category_name', 'N/A')}")
        print()
    
    # Testar também busca direta na família Revestimento
    print("\n=== TESTE FAMÍLIA REVESTIMENTO ===")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.name, pf.name as family_name, pc.name as category_name
        FROM products p
        JOIN product_categories pc ON p.category_id = pc.id
        JOIN product_families pf ON pc.family_id = pf.id
        WHERE pf.name = 'Revestimento'
    """)
    
    revestimento_products = cursor.fetchall()
    print(f"Produtos da família Revestimento: {len(revestimento_products)}")
    
    for p in revestimento_products:
        print(f"  • ID: {p[0]} | {p[1][:50]}...")
        print(f"    Categoria: {p[3]}")
    
    conn.close()
    
    # Verificar regras de seleção
    print("\n=== VERIFICAR REGRAS ===")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sr.id, sr.product_id, sr.condition_type, sr.condition_value, p.name
        FROM selection_rules sr
        JOIN products p ON sr.product_id = p.id
        WHERE sr.condition_value = 'ceramica'
    """)
    
    rules = cursor.fetchall()
    print(f"Regras para 'ceramica': {len(rules)}")
    for rule in rules:
        print(f"  • Regra {rule[0]}: Produto {rule[1]} ({rule[4][:30]}...) | {rule[2]}={rule[3]}")
    
    conn.close()

if __name__ == "__main__":
    debug_ceramic_selection()
