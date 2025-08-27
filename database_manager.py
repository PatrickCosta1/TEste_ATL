# Sistema de Gestão da Base de Dados
# Classe principal para gerir a base de dados de produtos

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import os
import sys
try:
    from default_data import products, product_families, product_categories
except ImportError:
    products = []
    product_families = []
    product_categories = []
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
        """Obtém produtos por categoria, com fallback para dados default"""
        try:
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
            products_list = []
            for row in cursor.fetchall():
                product = dict(row)
                product['attributes'] = self.get_product_attributes(product['id'])
                products_list.append(product)
            conn.close()
            if products_list:
                return products_list
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")
        # Fallback para dados default
        cat = next((c for c in product_categories if c['id'] == category_id), None)
        fam = next((f for f in product_families if cat and f['id'] == cat['family_id']), None)
        result = []
        for prod in products:
            if prod.get('category_id') == category_id and prod.get('is_active', 1):
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat['name'] if cat else None
                prod_copy['family_name'] = fam['name'] if fam else None
                prod_copy['attributes'] = self.get_product_attributes(prod['id'])
                result.append(prod_copy)
        return result
    
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
        """Encontra produtos que atendem às condições especificadas, com fallback para dados default_data.py"""
        try:
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
            products_list = []
            for row in cursor.fetchall():
                product = dict(row)
                product['attributes'] = self.get_product_attributes(product['id'])
                products_list.append(product)
            conn.close()
            if products_list:
                return products_list
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")

        # Fallback para dados default_data.py
        try:
            from default_data import products, product_categories, product_families, product_attributes, attribute_types
        except ImportError:
            products = globals().get('products', [])
            product_categories = globals().get('product_categories', [])
            product_families = globals().get('product_families', [])
            product_attributes = globals().get('product_attributes', [])
            attribute_types = globals().get('attribute_types', [])

        print(f"[DEBUG Render] Produtos carregados: {len(products)} | Categorias: {len(product_categories)} | Famílias: {len(product_families)} | Atributos: {len(product_attributes)} | Tipos de atributo: {len(attribute_types)}")

        # Fallback: retorna todos os produtos ativos que "batem" com as condições
        result = []
        for prod in products:
            if not prod.get('is_active', 1):
                continue
            # Para cada condição, tentar filtrar por atributo ou campo
            match = True
            for cond_key, cond_val in conditions.items():
                # Tenta por atributo
                attrs = [pa for pa in product_attributes if pa['product_id'] == prod['id']]
                attr_match = False
                for pa in attrs:
                    attr_type = next((a for a in attribute_types if a['id'] == pa['attribute_type_id']), None)
                    if attr_type and attr_type['name'].lower() == cond_key.lower():
                        # Comparação flexível (str)
                        v = pa.get('value_text') or pa.get('value_numeric') or pa.get('value_boolean')
                        if str(v).lower() == str(cond_val).lower():
                            attr_match = True
                            break
                # Se não bateu por atributo, tenta por campo direto
                if not attr_match:
                    # Exemplo: location pode ser campo 'localizacao' ou similar
                    if cond_key in prod and str(prod[cond_key]).lower() == str(cond_val).lower():
                        attr_match = True
                if not attr_match:
                    match = False
                    break
            if match:
                # Adiciona categoria/família/atributos
                cat = next((c for c in product_categories if c['id'] == prod['category_id']), None)
                fam = next((f for f in product_families if cat and f['id'] == cat['family_id']), None)
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat['name'] if cat else None
                prod_copy['family_name'] = fam['name'] if fam else None
                # Monta atributos
                prod_copy['attributes'] = {}
                for pa in product_attributes:
                    if pa['product_id'] == prod['id']:
                        attr_type = next((a for a in attribute_types if a['id'] == pa['attribute_type_id']), None)
                        if not attr_type:
                            continue
                        name = attr_type['name']
                        data_type = attr_type['data_type']
                        unit = attr_type.get('unit')
                        if data_type == 'numeric':
                            prod_copy['attributes'][name] = {'value': pa['value_numeric'], 'unit': unit}
                        elif data_type == 'boolean':
                            prod_copy['attributes'][name] = pa['value_boolean']
                        else:
                            prod_copy['attributes'][name] = pa['value_text']
                result.append(prod_copy)
        print(f"[DEBUG Render] Produtos retornados pelo fallback: {len(result)}")
        return result
    
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
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Busca um produto específico pelo ID, com fallback para dados default"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
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
                product['attributes'] = self.get_product_attributes(int(product['id']))
                conn.close()
                return product
            conn.close()
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")
        # Fallback para dados default
        for prod in products:
            if str(prod['id']) == str(product_id) and prod.get('is_active', 1):
                # Buscar categoria e família
                cat = next((c for c in product_categories if c['id'] == prod['category_id']), None)
                fam = next((f for f in product_families if cat and f['id'] == cat['family_id']), None)
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat['name'] if cat else None
                prod_copy['family_name'] = fam['name'] if fam else None
                prod_copy['attributes'] = self.get_product_attributes(prod['id'])
                return prod_copy
        return None
    
    def get_products_by_family(self, family_name: str) -> List[Dict]:
        """Busca todos os produtos de uma família específica, com fallback para dados default"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name, pf.name as family_name
                FROM products p
                JOIN product_categories pc ON p.category_id = pc.id
                JOIN product_families pf ON pc.family_id = pf.id
                WHERE pf.name = ? AND p.is_active = 1
                ORDER BY pc.display_order, p.name
            """, (family_name,))
            products_list = []
            for row in cursor.fetchall():
                product = dict(row)
                product['attributes'] = self.get_product_attributes(product['id'])
                products_list.append(product)
            conn.close()
            if products_list:
                return products_list
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")
        # Fallback para dados default
        fam = next((f for f in product_families if f['name'] == family_name), None)
        if not fam:
            return []
        fam_id = fam['id']
        cats = [c for c in product_categories if c['family_id'] == fam_id]
        cat_ids = [c['id'] for c in cats]
        result = []
        for prod in products:
            if prod.get('category_id') in cat_ids and prod.get('is_active', 1):
                cat = next((c for c in cats if c['id'] == prod['category_id']), None)
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat['name'] if cat else None
                prod_copy['family_name'] = fam['name']
                prod_copy['attributes'] = self.get_product_attributes(prod['id'])
                result.append(prod_copy)
        return result
    
    def get_all_families(self) -> List[Dict]:
        """Retorna todas as famílias de produtos disponíveis, com fallback para dados default"""
        try:
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
            if families:
                return families
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")
        # Fallback para dados default
        result = []
        for fam in product_families:
            fam_copy = fam.copy()
            fam_id = fam['id']
            cat_ids = [c['id'] for c in product_categories if c['family_id'] == fam_id]
            fam_copy['product_count'] = sum(1 for p in products if p.get('category_id') in cat_ids and p.get('is_active', 1))
            result.append(fam_copy)
        return result
    def get_product_attributes(self, product_id: int) -> Dict[str, Any]:
        """Obtém atributos de um produto, com fallback para dados default_data.py"""
        try:
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
            if attributes:
                return attributes
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")
        # Fallback para dados default
        # Tenta importar se não estiver no escopo
        try:
            from default_data import product_attributes, attribute_types
        except ImportError:
            product_attributes = globals().get('product_attributes', [])
            attribute_types = globals().get('attribute_types', [])
        attrs = {}
        for pa in product_attributes:
            if pa['product_id'] == product_id:
                attr_type = next((a for a in attribute_types if a['id'] == pa['attribute_type_id']), None)
                if not attr_type:
                    continue
                name = attr_type['name']
                data_type = attr_type['data_type']
                unit = attr_type.get('unit')
                if data_type == 'numeric':
                    attrs[name] = {'value': pa['value_numeric'], 'unit': unit}
                elif data_type == 'boolean':
                    attrs[name] = pa['value_boolean']
                else:
                    attrs[name] = pa['value_text']
        return attrs
