#!/usr/bin/env python3
"""
Script para reorganizar as famílias de produtos:
- Manter apenas Filtração
- Criar nova família: Recirculação e Iluminação - Encastráveis Tanque Piscina
- Adicionar todos os produtos da nova família
"""

from database_manager import DatabaseManager
import sqlite3

def reorganize_product_families():
    """Reorganiza as famílias de produtos conforme solicitado"""
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        print("🗄️ REORGANIZANDO FAMÍLIAS DE PRODUTOS")
        print("=" * 50)
        
        # 1. LIMPAR FAMÍLIAS DESNECESSÁRIAS (manter apenas Filtração)
        print("🗑️ Removendo famílias desnecessárias...")
        
        # Manter apenas a família Filtração (ID: 1)
        cursor.execute("DELETE FROM products WHERE category_id IN (SELECT id FROM product_categories WHERE family_id != 1)")
        cursor.execute("DELETE FROM product_categories WHERE family_id != 1") 
        cursor.execute("DELETE FROM product_families WHERE id != 1")
        
        print("✅ Famílias limpas - mantida apenas Filtração")
        
        # 2. CRIAR NOVA FAMÍLIA
        print("\n🏗️ Criando nova família...")
        
        cursor.execute("""
            INSERT INTO product_families (name, display_order, description) 
            VALUES ('Recirculação e Iluminação - Encastráveis Tanque Piscina', 2, 'Produtos para recirculação de água e iluminação encastráveis')
        """)
        
        new_family_id = cursor.lastrowid
        print(f"✅ Nova família criada com ID: {new_family_id}")
        
        # 3. CRIAR CATEGORIAS PARA A NOVA FAMÍLIA
        categories = [
            ('Skimmers', 1),
            ('Bocas de Impulsão', 2), 
            ('Tomadas de Aspiração', 3),
            ('Acessórios Hidráulicos', 4),
            ('Reguladores de Nível', 5),
            ('Ralos de Fundo', 6),
            ('Iluminação LED', 7)
        ]
        
        category_ids = {}
        for cat_name, order in categories:
            cursor.execute("""
                INSERT INTO product_categories (family_id, name, display_order)
                VALUES (?, ?, ?)
            """, (new_family_id, cat_name, order))
            category_ids[cat_name] = cursor.lastrowid
            print(f"✅ Categoria '{cat_name}' criada")
        
        # 4. INSERIR PRODUTOS
        print(f"\n📦 Inserindo produtos...")
        
        # SKIMMERS
        skimmers = [
            ("Skimmer Classis Boca Larga Branco Liner", "SK-CL-BL-LINER", 135.00, {"Material": "Plástico", "Tipo": "Liner", "Modelo": "Classic"}),
            ("Skimmer Standard Branco Liner", "SK-STD-LINER", 104.00, {"Material": "Plástico", "Tipo": "Liner", "Modelo": "Standard"}),
            ("Skimmer Linha de água Branco Liner", "SK-LDA-LINER", 210.00, {"Material": "Plástico", "Tipo": "Liner", "Modelo": "Linha de Água"}),
            ("Skimmer Classis Boca Larga Branco Betão", "SK-CL-BL-BETAO", 103.00, {"Material": "Plástico", "Tipo": "Betão", "Modelo": "Classic"}),
            ("Skimmer Standard Branco Betão", "SK-STD-BETAO", 73.20, {"Material": "Plástico", "Tipo": "Betão", "Modelo": "Standard"}),
            ("Skimmer Linha de água Branco Betão", "SK-LDA-BETAO", 165.00, {"Material": "Plástico", "Tipo": "Betão", "Modelo": "Linha de Água"}),
            ("Skimmer Standard em Aço inox AISI 316L Liner", "SK-STD-INOX-LINER", 1985.00, {"Material": "Aço Inox AISI 316L", "Tipo": "Liner", "Modelo": "Standard"}),
            ("Skimmer Standard Boca Larga em Aço inox AISI 316L Liner", "SK-STD-BL-INOX-LINER", 2147.00, {"Material": "Aço Inox AISI 316L", "Tipo": "Liner", "Modelo": "Standard Boca Larga"}),
            ("Skimmer Standard em Aço inox AISI 316L Betão", "SK-STD-INOX-BETAO", 1453.00, {"Material": "Aço Inox AISI 316L", "Tipo": "Betão", "Modelo": "Standard"}),
            ("Skimmer Standard Boca Larga em Aço inox AISI 316L Betão", "SK-STD-BL-INOX-BETAO", 1558.00, {"Material": "Aço Inox AISI 316L", "Tipo": "Betão", "Modelo": "Standard Boca Larga"}),
        ]
        
        # BOCAS DE IMPULSÃO
        bocas_impulsao = [
            ("Boca de Impulsão de parede Astralpool Liner", "BI-PAR-AST-LINER", 14.25, {"Tipo": "Parede", "Material": "Plástico", "Instalação": "Liner"}),
            ("Boca de Impulsão de parede em Aço inox AISI 316L Liner", "BI-PAR-INOX-LINER", 196.00, {"Tipo": "Parede", "Material": "Aço Inox AISI 316L", "Instalação": "Liner"}),
            ("Boca de Impulsão de parede Astralpool Betão", "BI-PAR-AST-BETAO", 8.55, {"Tipo": "Parede", "Material": "Plástico", "Instalação": "Betão"}),
            ("Boca de Impulsão de parede em Aço inox AISI 316L Betão", "BI-PAR-INOX-BETAO", 147.00, {"Tipo": "Parede", "Material": "Aço Inox AISI 316L", "Instalação": "Betão"}),
            ("Boca de impulsão de fundo Astralpool Liner", "BI-FUN-AST-LINER", 24.95, {"Tipo": "Fundo", "Material": "Plástico", "Instalação": "Liner"}),
            ("Boca de impulsão de fundo em aço inox AISI 316L Liner", "BI-FUN-INOX-LINER", 196.00, {"Tipo": "Fundo", "Material": "Aço Inox AISI 316L", "Instalação": "Liner"}),
            ("Boca de impulsão de fundo Astralpool Betão", "BI-FUN-AST-BETAO", 12.80, {"Tipo": "Fundo", "Material": "Plástico", "Instalação": "Betão"}),
            ("Boca de impulsão de fundo em aço inox AISI 316L Betão", "BI-FUN-INOX-BETAO", 136.00, {"Tipo": "Fundo", "Material": "Aço Inox AISI 316L", "Instalação": "Betão"}),
        ]
        
        # TOMADAS DE ASPIRAÇÃO
        tomadas_aspiracao = [
            ("Tomada de Aspiração Astralpool Liner", "TA-AST-LINER", 23.30, {"Material": "Plástico", "Instalação": "Liner"}),
            ("Tomada de Aspiração Astralpool Betão", "TA-AST-BETAO", 8.60, {"Material": "Plástico", "Instalação": "Betão"}),
            ("Aspiração Branco com joelho 90º", "TA-JOELHO-90", 48.50, {"Material": "Plástico", "Acessórios": "Joelho 90º"}),
        ]
        
        # ACESSÓRIOS HIDRÁULICOS
        acessorios = [
            ("Passamuros Astralpool Liner", "PM-AST-LINER", 13.90, {"Tipo": "Passamuros", "Instalação": "Liner"}),
            ("Passamuros Astralpool Betão", "PM-AST-BETAO", 13.90, {"Tipo": "Passamuros", "Instalação": "Betão"}),
        ]
        
        # REGULADORES DE NÍVEL
        reguladores = [
            ("Regulador de Nível mecânico Kripsol", "RN-MEC-KRIPSOL", 199.00, {"Tipo": "Mecânico", "Marca": "Kripsol"}),
            ("Regulador de Nível mecânico Wise", "RN-MEC-WISE", 199.00, {"Tipo": "Mecânico", "Marca": "Wise"}),
            ("Regulador de Nível Astralpool", "RN-AST", 199.00, {"Tipo": "Standard", "Marca": "Astralpool"}),
        ]
        
        # RALOS DE FUNDO
        ralos = [
            ("Ralo de fundo circular 290mm com insertos Astralpool Liner", "RF-CIRC-290-LINER", 78.00, {"Diâmetro": "290mm", "Tipo": "Circular", "Instalação": "Liner"}),
            ("Ralo de fundo Kripsol Liner", "RF-KRIPSOL-LINER", 46.35, {"Marca": "Kripsol", "Instalação": "Liner"}),
            ("Ralo de fundo redondo em aço inox AISI 316L Liner", "RF-INOX-LINER", 797.00, {"Material": "Aço Inox AISI 316L", "Tipo": "Redondo", "Instalação": "Liner"}),
            ("Ralo de fundo cicular 270mm Astralpool Betão", "RF-CIRC-270-BETAO", 46.00, {"Diâmetro": "270mm", "Tipo": "Circular", "Instalação": "Betão"}),
            ("Ralo de fundo Kripsol Betão", "RF-KRIPSOL-BETAO", 23.30, {"Marca": "Kripsol", "Instalação": "Betão"}),
            ("Ralo de fundo redondo em aço inox AISI 316L Betão", "RF-INOX-BETAO", 596.00, {"Material": "Aço Inox AISI 316L", "Tipo": "Redondo", "Instalação": "Betão"}),
        ]
        
        # ILUMINAÇÃO LED
        iluminacao = [
            ("Projector Led Luz Branca de 50mm", "LED-BRANCO-50", 247.00, {"Tipo": "Branca", "Diâmetro": "50mm", "Tecnologia": "LED"}),
            ("Projector Led Luz Branca de 100mm", "LED-BRANCO-100", 343.00, {"Tipo": "Branca", "Diâmetro": "100mm", "Tecnologia": "LED"}),
            ("Projector Led Luz Branca de 170mm", "LED-BRANCO-170", 437.00, {"Tipo": "Branca", "Diâmetro": "170mm", "Tecnologia": "LED"}),
            ("Projector Led Luz Branco Adaptável de 50mm", "LED-ADAPTAVEL-50", 266.00, {"Tipo": "Branco Adaptável", "Diâmetro": "50mm", "Tecnologia": "LED"}),
            ("Projector Led Luz Branco Adaptável de 100mm", "LED-ADAPTAVEL-100", 380.00, {"Tipo": "Branco Adaptável", "Diâmetro": "100mm", "Tecnologia": "LED"}),
            ("Projector Led Luz Branco Adaptável de 170mm", "LED-ADAPTAVEL-170", 480.00, {"Tipo": "Branco Adaptável", "Diâmetro": "170mm", "Tecnologia": "LED"}),
            ("Projector Led Luz RGB de 50mm", "LED-RGB-50", 282.00, {"Tipo": "RGB", "Diâmetro": "50mm", "Tecnologia": "LED"}),
            ("Projector Led Luz RGB de 100mm", "LED-RGB-100", 423.00, {"Tipo": "RGB", "Diâmetro": "100mm", "Tecnologia": "LED"}),
            ("Projector Led Luz RGB de 170mm", "LED-RGB-170", 480.00, {"Tipo": "RGB", "Diâmetro": "170mm", "Tecnologia": "LED"}),
        ]
        
        # Lista de todos os produtos com suas categorias
        all_products = [
            (skimmers, 'Skimmers'),
            (bocas_impulsao, 'Bocas de Impulsão'),
            (tomadas_aspiracao, 'Tomadas de Aspiração'),
            (acessorios, 'Acessórios Hidráulicos'),
            (reguladores, 'Reguladores de Nível'),
            (ralos, 'Ralos de Fundo'),
            (iluminacao, 'Iluminação LED')
        ]
        
        total_products = 0
        for products, category_name in all_products:
            cat_id = category_ids[category_name]
            for name, code, price, attributes in products:
                # Inserir produto
                cursor.execute("""
                    INSERT INTO products (category_id, name, code, base_price, unit, is_active, brand, description)
                    VALUES (?, ?, ?, ?, 'un', 1, 'Astralpool', ?)
                """, (cat_id, name, code, price, f"Produto de recirculação/iluminação - {name}"))
                
                product_id = cursor.lastrowid
                
                # Inserir atributos
                for attr_name, attr_value in attributes.items():
                    # Verificar se o tipo de atributo existe
                    cursor.execute("SELECT id FROM attribute_types WHERE name = ?", (attr_name,))
                    result = cursor.fetchone()
                    
                    if not result:
                        # Criar tipo de atributo se não existir
                        cursor.execute("""
                            INSERT INTO attribute_types (name, data_type, unit, description)
                            VALUES (?, 'text', '', ?)
                        """, (attr_name, f"Atributo {attr_name}"))
                        attr_type_id = cursor.lastrowid
                    else:
                        attr_type_id = result[0]
                    
                    # Inserir atributo do produto (usando value_text)
                    cursor.execute("""
                        INSERT INTO product_attributes (product_id, attribute_type_id, value_text, value_numeric, value_boolean)
                        VALUES (?, ?, ?, 0, 0)
                    """, (product_id, attr_type_id, str(attr_value)))
                
                total_products += 1
                print(f"✅ {name} - €{price}")
        
        # Commit todas as alterações
        conn.commit()
        
        print(f"\n🎉 REORGANIZAÇÃO CONCLUÍDA!")
        print(f"✅ Total de produtos adicionados: {total_products}")
        print(f"✅ Nova família: Recirculação e Iluminação - Encastráveis Tanque Piscina")
        print(f"✅ Mantida família: Filtração")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    reorganize_product_families()
