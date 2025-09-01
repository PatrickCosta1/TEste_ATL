#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

def add_ceramic_category_and_products():
    conn = sqlite3.connect('database/pool_budgets.db')
    cursor = conn.cursor()
    
    try:
        # 1. Buscar o ID da família Revestimento
        cursor.execute("SELECT id FROM product_families WHERE name = 'Revestimento'")
        family_row = cursor.fetchone()
        if not family_row:
            print("Família 'Revestimento' não encontrada!")
            return
        family_id = family_row[0]
        print(f"Família Revestimento ID: {family_id}")
        
        # 2. Verificar se já existe categoria "Cerâmica"
        cursor.execute("SELECT id FROM product_categories WHERE family_id = ? AND name = 'Cerâmica'", (family_id,))
        ceramic_category = cursor.fetchone()
        
        if ceramic_category:
            category_id = ceramic_category[0]
            print(f"Categoria 'Cerâmica' já existe com ID: {category_id}")
        else:
            # 3. Criar categoria "Cerâmica"
            cursor.execute("""
                INSERT INTO product_categories (family_id, name, description, display_order, is_active)
                VALUES (?, 'Cerâmica', 'Produtos para revestimento cerâmico', 30, 1)
            """, (family_id,))
            category_id = cursor.lastrowid
            print(f"Categoria 'Cerâmica' criada com ID: {category_id}")
        
        # 4. Adicionar produto fixo: Impermeabilização
        impermeabilizacao_name = "Fornecimento de mão de obra e material para Impermeabilização de paredes e lage inferior com massa cinza, rede50 e banda Weberdry - 2 camadas"
        
        # Verificar se já existe
        cursor.execute("SELECT id FROM products WHERE name = ?", (impermeabilizacao_name,))
        existing = cursor.fetchone()
        if existing:
            product_id_1 = existing[0]
            print(f"Produto de impermeabilização já existe com ID: {product_id_1}")
        else:
            cursor.execute("""
                INSERT INTO products 
                (category_id, code, name, base_price, cost_price, brand, model, unit, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                category_id,
                "IMPER-CERAMIC-01",
                impermeabilizacao_name,
                0.0,  # Preço inicial 0, será editável
                0.0,  # Custo inicial 0, será editável
                "",
                "",
                "m2",
                "Impermeabilização para revestimento cerâmico com massa cinza, rede50 e banda Weberdry em 2 camadas",
            ))
            product_id_1 = cursor.lastrowid
            print(f"Produto impermeabilização criado com ID: {product_id_1}")
        
        # 5. Adicionar produto variável: Item personalizável
        custom_name = "Item Cerâmico Personalizado"
        
        # Verificar se já existe
        cursor.execute("SELECT id FROM products WHERE name = ?", (custom_name,))
        existing = cursor.fetchone()
        if existing:
            product_id_2 = existing[0]
            print(f"Produto personalizado já existe com ID: {product_id_2}")
        else:
            cursor.execute("""
                INSERT INTO products 
                (category_id, code, name, base_price, cost_price, brand, model, unit, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                category_id,
                "CUSTOM-CERAMIC-01",
                custom_name,
                0.0,  # Preço inicial 0, será editável
                0.0,  # Custo inicial 0, será editável
                "",
                "",
                "un",
                "Item personalizável para revestimento cerâmico - nome e preço editáveis",
            ))
            product_id_2 = cursor.lastrowid
            print(f"Produto personalizado criado com ID: {product_id_2}")
        
        # 6. Adicionar regras de seleção para revestimento cerâmico
        for product_id in [product_id_1, product_id_2]:
            cursor.execute("""
                INSERT OR IGNORE INTO selection_rules 
                (product_id, rule_name, condition_type, condition_value, operator, priority, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (product_id, "coating_ceramic", "coating_type", "ceramico", "=", 1))
        
        conn.commit()
        print("\n✅ Produtos cerâmicos adicionados com sucesso!")
        
        # Listar produtos criados
        print("\n=== PRODUTOS CERÂMICOS ===")
        cursor.execute("""
            SELECT p.id, p.code, p.name, p.base_price
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE pc.name = 'Cerâmica'
        """)
        
        for row in cursor.fetchall():
            print(f"ID: {row[0]} | Código: {row[1]} | Nome: {row[2][:50]}{'...' if len(row[2]) > 50 else ''}")
            print(f"  Preço: €{row[3]}")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_ceramic_category_and_products()
