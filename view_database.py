#!/usr/bin/env python3
"""
Visualizador da Base de Dados - Mostra todos os dados de forma organizada
"""

from database_manager import DatabaseManager
import json

def main():
    print("🗄️  VISUALIZADOR DA BASE DE DADOS - SISTEMA DE ORÇAMENTAÇÃO")
    print("=" * 80)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. FAMÍLIAS DE PRODUTOS
    print("\n📁 FAMÍLIAS DE PRODUTOS")
    print("-" * 40)
    cursor.execute("SELECT * FROM product_families ORDER BY display_order, name")
    families = cursor.fetchall()
    
    if families:
        for family in families:
            print(f"🏷️  {family['name']} (ID: {family['id']}, Ordem: {family['display_order']})")
    else:
        print("❌ Nenhuma família encontrada")
    
    # 2. CATEGORIAS DE PRODUTOS
    print("\n📂 CATEGORIAS DE PRODUTOS")
    print("-" * 40)
    cursor.execute("""
        SELECT pc.*, pf.name as family_name 
        FROM product_categories pc
        LEFT JOIN product_families pf ON pc.family_id = pf.id
        ORDER BY pf.display_order, pc.display_order, pc.name
    """)
    categories = cursor.fetchall()
    
    if categories:
        current_family = None
        for category in categories:
            if category['family_name'] != current_family:
                current_family = category['family_name']
                print(f"\n  📁 {current_family or 'Sem Família'}")
            print(f"    📂 {category['name']} (ID: {category['id']}, Ordem: {category['display_order']})")
    else:
        print("❌ Nenhuma categoria encontrada")
    
    # 3. PRODUTOS POR FAMÍLIA
    print("\n\n🛒 PRODUTOS POR FAMÍLIA")
    print("=" * 80)
    
    for family in families:
        family_name = family['name']
        print(f"\n📁 FAMÍLIA: {family_name}")
        print("-" * 60)
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE pc.family_id = ? AND p.is_active = 1
            ORDER BY pc.display_order, p.name
        """, (family['id'],))
        
        products = cursor.fetchall()
        
        if products:
            current_category = None
            for product in products:
                if product['category_name'] != current_category:
                    current_category = product['category_name']
                    print(f"\n  📂 {current_category}")
                
                print(f"    📦 {product['name']}")
                print(f"       💰 €{product['base_price']:,.2f}")
                print(f"       🏷️  Código: {product['code']}")
                print(f"       📏 Unidade: {product['unit']}")
                
                # Mostrar atributos
                attributes = db.get_product_attributes(product['id'])
                if attributes:
                    print(f"       📋 Atributos:")
                    for attr_name, attr_value in attributes.items():
                        if isinstance(attr_value, dict):
                            value_str = f"{attr_value.get('value', 'N/A')}"
                            if 'unit' in attr_value and attr_value['unit']:
                                value_str += f" {attr_value['unit']}"
                        else:
                            value_str = str(attr_value)
                        print(f"          • {attr_name}: {value_str}")
                
                # Mostrar regras de seleção
                cursor.execute("""
                    SELECT * FROM selection_rules 
                    WHERE product_id = ? AND is_active = 1
                    ORDER BY priority DESC
                """, (product['id'],))
                rules = cursor.fetchall()
                
                if rules:
                    print(f"       🎯 Regras de Seleção:")
                    for rule in rules:
                        print(f"          • {rule['condition_type']} {rule['operator']} {rule['condition_value']} (Prioridade: {rule['priority']})")
                
                if product['description']:
                    print(f"       📝 {product['description']}")
                
                print()
        else:
            print("    ❌ Nenhum produto nesta família")
    
    # 4. RESUMO ESTATÍSTICO
    print("\n📊 RESUMO ESTATÍSTICO")
    print("-" * 40)
    
    # Contar por família
    cursor.execute("""
        SELECT pf.name as family_name, COUNT(p.id) as total_products
        FROM product_families pf
        LEFT JOIN product_categories pc ON pf.id = pc.family_id
        LEFT JOIN products p ON pc.id = p.category_id AND p.is_active = 1
        GROUP BY pf.id, pf.name
        ORDER BY total_products DESC, pf.name
    """)
    
    family_stats = cursor.fetchall()
    for stat in family_stats:
        print(f"📁 {stat['family_name']}: {stat['total_products']} produtos")
    
    # Total geral
    cursor.execute("SELECT COUNT(*) as total FROM products WHERE is_active = 1")
    total_products = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM product_categories")
    total_categories = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM product_families")
    total_families = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM selection_rules WHERE is_active = 1")
    total_rules = cursor.fetchone()['total']
    
    print(f"\n🎯 TOTAIS:")
    print(f"   • {total_families} famílias")
    print(f"   • {total_categories} categorias")
    print(f"   • {total_products} produtos ativos")
    print(f"   • {total_rules} regras de seleção ativas")
    
    # 5. FAIXA DE PREÇOS
    print(f"\n💰 FAIXA DE PREÇOS:")
    cursor.execute("""
        SELECT 
            MIN(base_price) as min_price,
            MAX(base_price) as max_price,
            AVG(base_price) as avg_price
        FROM products 
        WHERE is_active = 1 AND base_price > 0
    """)
    price_stats = cursor.fetchone()
    
    if price_stats and price_stats['min_price']:
        print(f"   • Mínimo: €{price_stats['min_price']:,.2f}")
        print(f"   • Máximo: €{price_stats['max_price']:,.2f}")
        print(f"   • Média: €{price_stats['avg_price']:,.2f}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ Visualização completa da base de dados!")

if __name__ == "__main__":
    main()
