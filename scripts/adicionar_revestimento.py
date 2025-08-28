#!/usr/bin/env python3
"""
Script para adicionar a família "Revestimento" e seus produtos
"""

from database_manager import DatabaseManager

def main():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # 1. Criar a família Revestimento
    cursor.execute("""
        INSERT OR IGNORE INTO product_families (name, description, display_order)
        VALUES (?, ?, ?)
    """, ('Revestimento', 'Produtos de revestimento para piscinas', 4))
    
    # Buscar ID da família
    cursor.execute("SELECT id FROM product_families WHERE name = 'Revestimento'")
    family_result = cursor.fetchone()
    if not family_result:
        print("❌ Erro ao criar família Revestimento")
        return
    family_id = family_result['id']

    # 2. Criar categorias
    categorias = [
        ('Telas', 1),
        ('Perfis', 2)
    ]
    
    for categoria_nome, ordem in categorias:
        cursor.execute("""
            INSERT OR IGNORE INTO product_categories (family_id, name, display_order)
            VALUES (?, ?, ?)
        """, (family_id, categoria_nome, ordem))

    # 3. Buscar IDs das categorias
    cursor.execute("SELECT id FROM product_categories WHERE family_id = ? AND name = 'Telas'", (family_id,))
    telas_id = cursor.fetchone()['id']
    
    cursor.execute("SELECT id FROM product_categories WHERE family_id = ? AND name = 'Perfis'", (family_id,))
    perfis_id = cursor.fetchone()['id']

    # 4. Adicionar produtos
    produtos = [
        # Telas (em rolos de 25m)
        (telas_id, 'TELA-3D-UNICOLOR-CGT', 'Revestimento Tela Armada 3D Unicolor CGT', 1799.80, 'Vg', 'CGT'),
        (telas_id, 'TELA-3D-CGT', 'Revestimento Tela Armada 3D CGT', 2428.80, 'Vg', 'CGT'),
        (telas_id, 'TELA-LISA-CGT', 'Revestimento Tela Armada Lisa CGT', 1760.00, 'Vg', 'CGT'),
        
        # Perfis
        (perfis_id, 'PERFIL-HORIZONTAL-2ML', 'Perfil Horizontal de Fixação (2ml)', 5.25, 'un', 'Genérico'),
        (perfis_id, 'PERFIL-VERTICAL-2ML', 'Perfil Vertical para Renovação (2ml)', 6.30, 'un', 'Genérico'),
        (perfis_id, 'CHAPA-COLAMINADA', 'Chapa Colaminada', 7.50, 'un', 'Genérico'),
    ]

    for categoria_id, codigo, nome, preco, unidade, marca in produtos:
        # Verificar se já existe
        cursor.execute("SELECT id FROM products WHERE code = ?", (codigo,))
        if cursor.fetchone():
            print(f"✅ Produto '{nome}' já existe")
            continue
            
        cursor.execute("""
            INSERT INTO products (
                category_id, code, name, description, brand, unit, base_price, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            categoria_id, codigo, nome,
            f'Produto de revestimento - {nome}',
            marca, unidade, preco, 1
        ))
        
        print(f"✅ Produto '{nome}' adicionado com sucesso!")

    conn.commit()
    conn.close()
    print("\n🎉 Família 'Revestimento' e todos os produtos foram adicionados com sucesso!")

if __name__ == "__main__":
    main()
