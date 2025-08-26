#!/usr/bin/env python3
"""
Script para adicionar o produto "Doseador Automático RX" na família Tratamento de Água
"""

from database_manager import DatabaseManager

def main():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Buscar ID da categoria "Químicos" na família "Tratamento de Água"
    cursor.execute("""
        SELECT pc.id 
        FROM product_categories pc
        JOIN product_families pf ON pc.family_id = pf.id
        WHERE pf.name = 'Tratamento de Água' AND pc.name = 'Químicos'
    """)
    
    categoria_result = cursor.fetchone()
    
    if not categoria_result:
        print("❌ Categoria 'Químicos' na família 'Tratamento de Água' não encontrada!")
        conn.close()
        return
    
    categoria_id = categoria_result['id']
    
    # Verificar se o produto já existe
    cursor.execute("""
        SELECT id FROM products 
        WHERE name = 'Doseador Automático RX'
    """)
    
    if cursor.fetchone():
        print("✅ Produto 'Doseador Automático RX' já existe na base de dados")
        conn.close()
        return
    
    # Adicionar o produto
    cursor.execute("""
        INSERT INTO products (
            category_id, code, name, description, brand, unit, base_price, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        categoria_id,
        'DOSEADOR-AUTOMATICO-RX',
        'Doseador Automático RX',
        'Produto de tratamento de água - Doseador Automático RX',
        'Genérica',
        'un',
        345.00,
        1
    ))
    
    produto_id = cursor.lastrowid
    
    # Adicionar atributos
    cursor.execute("""
        SELECT id FROM attribute_types WHERE name = 'Tipo'
    """)
    tipo_attr = cursor.fetchone()
    
    if tipo_attr:
        cursor.execute("""
            INSERT INTO product_attributes (product_id, attribute_type_id, value_text)
            VALUES (?, ?, ?)
        """, (produto_id, tipo_attr['id'], 'Doseador Automático'))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Produto 'Doseador Automático RX' adicionado com sucesso! ID: {produto_id}")

if __name__ == "__main__":
    main()
