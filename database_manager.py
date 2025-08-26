# Sistema de Gestão da Base de Dados
# Classe principal para gerir a base de dados de produtos

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import os
import sys

class DatabaseManager:
    """Gestor da base de dados de produtos e orçamentos"""
    
    def __init__(self, db_path: str = None):
        """Inicializa o gestor da base de dados com suporte a PyInstaller"""
        if db_path is None:
            # Detectar se estamos no executável PyInstaller
            if hasattr(sys, '_MEIPASS'):
                # No executável, a BD foi copiada para a pasta temporária
                db_path = os.path.join(sys._MEIPASS, 'pool_budgets.db')
                print(f"DEBUG: Executável detectado, usando BD em: {db_path}")
            else:
                # Em desenvolvimento, usar path relativo
                db_path = "database/pool_budgets.db"
                print(f"DEBUG: Desenvolvimento detectado, usando BD em: {db_path}")
        
        self.db_path = db_path
        print(f"DEBUG: Path final da BD: {self.db_path}")
        print(f"DEBUG: BD existe? {os.path.exists(self.db_path)}")
        
        if not os.path.exists(self.db_path):
            if hasattr(sys, '_MEIPASS'):
                # No executável, se não encontrar, tentar path alternativo
                alt_path = os.path.join(os.path.dirname(sys.executable), 'pool_budgets.db')
                if os.path.exists(alt_path):
                    self.db_path = alt_path
                    print(f"DEBUG: BD encontrada em path alternativo: {alt_path}")
                else:
                    raise FileNotFoundError(f"Base de dados não encontrada. Tentou: {db_path} e {alt_path}")
            else:
                # Em desenvolvimento, criar se não existir
                self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Garante que a base de dados existe e está inicializada"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if not os.path.exists(self.db_path):
            self.create_database()
            self.populate_initial_data()
    
    def create_database(self):
        """Cria a estrutura da base de dados"""
        schema_path = "database/schema.sql"
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executescript(schema)
            conn.commit()
            conn.close()
            print(f"Base de dados criada em: {self.db_path}")
    
    def get_connection(self):
        """Retorna conexão à base de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acesso por nome de coluna
        return conn
    
    # ==========================================
    # GESTÃO DE PRODUTOS
    # ==========================================
    
    def add_product(self, category_id: int, code: str, name: str, price: float, 
                   attributes: Dict[str, Any] = None, **kwargs) -> int:
        """Adiciona um novo produto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO products (category_id, code, name, base_price, brand, model, unit, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category_id, code, name, price,
                kwargs.get('brand', ''), kwargs.get('model', ''),
                kwargs.get('unit', 'un'), kwargs.get('description', '')
            ))
            
            product_id = cursor.lastrowid
            
            # Adicionar atributos se fornecidos
            if attributes:
                for attr_name, value in attributes.items():
                    self.add_product_attribute(product_id, attr_name, value, cursor)
            
            conn.commit()
            return product_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def add_product_attribute(self, product_id: int, attr_name: str, value: Any, cursor=None):
        """Adiciona atributo a um produto"""
        close_conn = cursor is None
        if cursor is None:
            conn = self.get_connection()
            cursor = conn.cursor()
        
        try:
            # Encontrar o tipo de atributo
            cursor.execute("SELECT id, data_type FROM attribute_types WHERE name = ?", (attr_name,))
            attr_type = cursor.fetchone()
            
            if not attr_type:
                # Criar tipo de atributo se não existe
                cursor.execute("INSERT INTO attribute_types (name, data_type) VALUES (?, ?)", 
                              (attr_name, self._detect_data_type(value)))
                attr_type_id = cursor.lastrowid
                data_type = self._detect_data_type(value)
            else:
                attr_type_id, data_type = attr_type
            
            # Inserir o atributo com o valor correto
            if data_type == 'numeric':
                cursor.execute("""
                    INSERT INTO product_attributes (product_id, attribute_type_id, value_numeric)
                    VALUES (?, ?, ?)
                """, (product_id, attr_type_id, float(value)))
            elif data_type == 'boolean':
                cursor.execute("""
                    INSERT INTO product_attributes (product_id, attribute_type_id, value_boolean)
                    VALUES (?, ?, ?)
                """, (product_id, attr_type_id, bool(value)))
            else:
                cursor.execute("""
                    INSERT INTO product_attributes (product_id, attribute_type_id, value_text)
                    VALUES (?, ?, ?)
                """, (product_id, attr_type_id, str(value)))
            
            if close_conn:
                conn.commit()
                
        finally:
            if close_conn and cursor:
                cursor.connection.close()
    
    def _detect_data_type(self, value) -> str:
        """Detecta o tipo de dados automaticamente"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, float)):
            return 'numeric'
        else:
            return 'text'
    
    def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Obtém produtos por categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name, pf.name as family_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            JOIN product_families pf ON pc.family_id = pf.id
            WHERE p.category_id = ? AND p.is_active = 1
            ORDER BY p.name
        """, (category_id,))
        
        products = []
        for row in cursor.fetchall():
            product = dict(row)
            product['attributes'] = self.get_product_attributes(product['id'])
            products.append(product)
        
        conn.close()
        return products
    
    def get_product_attributes(self, product_id: int) -> Dict[str, Any]:
        """Obtém atributos de um produto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT at.name, at.data_type, at.unit,
                   pa.value_numeric, pa.value_text, pa.value_boolean
            FROM product_attributes pa
            JOIN attribute_types at ON pa.attribute_type_id = at.id
            WHERE pa.product_id = ?
        """, (product_id,))
        
        attributes = {}
        for row in cursor.fetchall():
            name = row['name']
            if row['data_type'] == 'numeric':
                attributes[name] = {
                    'value': row['value_numeric'],
                    'unit': row['unit']
                }
            elif row['data_type'] == 'boolean':
                attributes[name] = row['value_boolean']
            else:
                attributes[name] = row['value_text']
        
        conn.close()
        return attributes
    
    # ==========================================
    # REGRAS DE SELEÇÃO
    # ==========================================
    
    def add_selection_rule(self, product_id: int, condition_type: str, 
                          condition_value: str, operator: str = '=', priority: int = 0):
        """Adiciona regra de seleção automática"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO selection_rules 
            (product_id, rule_name, condition_type, condition_value, operator, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, f"{condition_type}_{condition_value}", condition_type, 
              condition_value, operator, priority))
        
        conn.commit()
        conn.close()
    
    def get_products_by_conditions(self, conditions: Dict[str, Any]) -> List[Dict]:
        """Encontra produtos que atendem às condições especificadas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Query básica
        query = """
            SELECT DISTINCT p.*, pc.name as category_name, pf.name as family_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            JOIN product_families pf ON pc.family_id = pf.id
            JOIN selection_rules sr ON p.id = sr.product_id
            WHERE p.is_active = 1 AND sr.is_active = 1
        """
        
        conditions_sql = []
        params = []
        
        for condition_type, value in conditions.items():
            conditions_sql.append("(sr.condition_type = ? AND sr.condition_value = ?)")
            params.extend([condition_type, str(value)])
        
        if conditions_sql:
            query += " AND (" + " OR ".join(conditions_sql) + ")"
        
        query += " ORDER BY pf.display_order, pc.display_order, sr.priority DESC, p.name"
        
        cursor.execute(query, params)
        
        products = []
        for row in cursor.fetchall():
            product = dict(row)
            product['attributes'] = self.get_product_attributes(product['id'])
            products.append(product)
        
        conn.close()
        return products
    
    # ==========================================
    # GESTÃO DE ORÇAMENTOS
    # ==========================================
    
    def create_budget(self, pool_specs: Dict, answers: Dict, items: List[Dict]) -> int:
        """Cria um novo orçamento completo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Gerar número do orçamento
            budget_number = f"ORC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Criar cabeçalho
            cursor.execute("""
                INSERT INTO budgets (budget_number, status, created_at)
                VALUES (?, 'draft', ?)
            """, (budget_number, datetime.now()))
            
            budget_id = cursor.lastrowid
            
            # Especificações da piscina
            cursor.execute("""
                INSERT INTO budget_pool_specs 
                (budget_id, length, width, depth_min, depth_max, depth_avg, volume, m3_per_hour,
                 access_level, has_excavation, shape, pool_type, coating_type, has_domotics, 
                 location, power_type, calculated_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                budget_id,
                pool_specs['comprimento'], pool_specs['largura'],
                pool_specs['prof_min'], pool_specs['prof_max'],
                pool_specs.get('prof_media'), pool_specs.get('volume'),
                pool_specs.get('m3_h'),
                answers.get('acesso'), answers.get('escavacao'),
                answers.get('forma'), answers.get('tipo_piscina'),
                answers.get('revestimento'), answers.get('domotica'),
                answers.get('localizacao'), answers.get('luz'),
                json.dumps(pool_specs)
            ))
            
            # Itens do orçamento
            for item in items:
                cursor.execute("""
                    INSERT INTO budget_items 
                    (budget_id, product_id, quantity, unit_price, total_price, is_optional, selection_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    budget_id, item['product_id'], item['quantity'],
                    item['unit_price'], item['total_price'],
                    item.get('is_optional', False), item.get('reasoning', '')
                ))
            
            conn.commit()
            return budget_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def populate_initial_data(self):
        """Popula dados iniciais na base de dados"""
        print("A carregar dados iniciais...")
        
        # Aqui você pode carregar dados de ficheiros CSV, JSON, etc.
        # Exemplo: carregar produtos de filtração
        self._load_filtration_products()
        print("Dados iniciais carregados com sucesso!")
    
    def _load_filtration_products(self):
        """Carrega produtos de filtração iniciais"""
        # Filtros de areia
        filters_sand = [
            {
                'code': 'FA-10', 'name': 'Filtro Areia 10 m³/h', 'price': 350.00,
                'attributes': {'Capacidade': 10, 'Tipo de Filtro': 'areia', 'Localização': 'exterior'}
            },
            {
                'code': 'FA-15', 'name': 'Filtro Areia 15 m³/h', 'price': 480.00,
                'attributes': {'Capacidade': 15, 'Tipo de Filtro': 'areia', 'Localização': 'exterior'}
            },
            {
                'code': 'FA-20', 'name': 'Filtro Areia 20 m³/h', 'price': 620.00,
                'attributes': {'Capacidade': 20, 'Tipo de Filtro': 'areia', 'Localização': 'exterior'}
            }
        ]
        
        # Filtros de cartucho  
        filters_cartridge = [
            {
                'code': 'FC-10', 'name': 'Filtro Cartucho 10 m³/h', 'price': 450.00,
                'attributes': {'Capacidade': 10, 'Tipo de Filtro': 'cartucho', 'Localização': 'interior'}
            },
            {
                'code': 'FC-15', 'name': 'Filtro Cartucho 15 m³/h', 'price': 650.00,
                'attributes': {'Capacidade': 15, 'Tipo de Filtro': 'cartucho', 'Localização': 'interior'}
            }
        ]
        
        # Adicionar produtos (categoria 1 = Filtros de Areia, 2 = Filtros de Cartucho)
        for filter_data in filters_sand:
            product_id = self.add_product(1, **filter_data)
            # Adicionar regras de seleção
            self.add_selection_rule(product_id, 'location', 'exterior')
        
        for filter_data in filters_cartridge:
            product_id = self.add_product(2, **filter_data)
            self.add_selection_rule(product_id, 'location', 'interior')
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Busca um produto específico pelo ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print(f"DEBUG get_product_by_id: Procurando produto ID={product_id} (tipo: {type(product_id)})")
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name, pf.name as family_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            JOIN product_families pf ON pc.family_id = pf.id
            WHERE p.id = ? AND p.is_active = 1
        """, (product_id,))
        
        row = cursor.fetchone()
        
        if row:
            product = dict(row)
            print(f"DEBUG: Produto encontrado - {product['name']} (categoria: {product['category_name']}, família: {product['family_name']})")
            product['attributes'] = self.get_product_attributes(int(product['id']))
            conn.close()
            return product
        else:
            print(f"DEBUG: Nenhum produto encontrado com ID={product_id}")
            conn.close()
            return None
    
    def get_products_by_family(self, family_name: str) -> List[Dict]:
        """Busca todos os produtos de uma família específica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Buscar por nome da família exato
        cursor.execute("""
            SELECT p.*, pc.name as category_name, pf.name as family_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            JOIN product_families pf ON pc.family_id = pf.id
            WHERE pf.name = ? AND p.is_active = 1
            ORDER BY pc.display_order, p.name
        """, (family_name,))
        
        products = []
        for row in cursor.fetchall():
            product = dict(row)
            product['attributes'] = self.get_product_attributes(product['id'])
            products.append(product)
        
        conn.close()
        print(f"DEBUG: Encontrados {len(products)} produtos para família '{family_name}'")
        for p in products:
            print(f"  - {p['name']} (ID: {p['id']})")
        
        return products
    
    def get_all_families(self) -> List[Dict]:
        """Retorna todas as famílias de produtos disponíveis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pf.id, pf.name, pf.description, 
                   COUNT(p.id) as product_count
            FROM product_families pf
            LEFT JOIN product_categories pc ON pf.id = pc.family_id
            LEFT JOIN products p ON pc.id = p.category_id AND p.is_active = 1
            GROUP BY pf.id, pf.name, pf.description
            ORDER BY pf.display_order, pf.name
        """)
        
        families = []
        for row in cursor.fetchall():
            family = dict(row)
            families.append(family)
        
        conn.close()
        return families
