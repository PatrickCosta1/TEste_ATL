-- Schema para Sistema de Orçamentação de Piscinas
-- Base de dados completa com todas as tabelas necessárias

-- ==========================================
-- TABELAS PRINCIPAIS DE PRODUTOS
-- ==========================================

-- Categorias principais de produtos
CREATE TABLE product_families (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subcategorias dentro de cada família
CREATE TABLE product_categories (
    id INTEGER PRIMARY KEY,
    family_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (family_id) REFERENCES product_families(id)
);

-- Produtos individuais
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    brand VARCHAR(100),
    model VARCHAR(100),
    unit VARCHAR(20) DEFAULT 'un',
    base_price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES product_categories(id)
);

-- ==========================================
-- ESPECIFICAÇÕES E ATRIBUTOS
-- ==========================================

-- Tipos de atributos (capacidade, voltagem, etc.)
CREATE TABLE attribute_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- 'numeric', 'text', 'boolean', 'select'
    unit VARCHAR(20),
    description TEXT
);

-- Atributos específicos de cada produto
CREATE TABLE product_attributes (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    attribute_type_id INTEGER NOT NULL,
    value_numeric DECIMAL(10,4),
    value_text VARCHAR(200),
    value_boolean BOOLEAN,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (attribute_type_id) REFERENCES attribute_types(id)
);

-- ==========================================
-- REGRAS DE SELEÇÃO
-- ==========================================

-- Condições para seleção automática
CREATE TABLE selection_rules (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    condition_type VARCHAR(50) NOT NULL, -- 'location', 'pool_type', 'capacity', 'domotics', etc.
    condition_value VARCHAR(100),
    operator VARCHAR(20) DEFAULT '=', -- '=', '>', '<', '>=', '<=', 'IN', 'NOT IN'
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Produtos alternativos/opcionais
CREATE TABLE product_alternatives (
    id INTEGER PRIMARY KEY,
    primary_product_id INTEGER NOT NULL,
    alternative_product_id INTEGER NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'upgrade', 'optional', 'substitute'
    price_difference DECIMAL(10,2) DEFAULT 0,
    conditions TEXT, -- JSON com condições específicas
    FOREIGN KEY (primary_product_id) REFERENCES products(id),
    FOREIGN KEY (alternative_product_id) REFERENCES products(id)
);

-- ==========================================
-- MULTIPLICADORES E PREÇOS
-- ==========================================

-- Regras de multiplicadores
CREATE TABLE price_multipliers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    condition_type VARCHAR(50) NOT NULL,
    condition_value VARCHAR(100),
    multiplier DECIMAL(5,3) NOT NULL,
    applies_to VARCHAR(50) DEFAULT 'all', -- 'all', 'family', 'category', 'product'
    target_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- Preços especiais por região/cliente
CREATE TABLE special_prices (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    client_type VARCHAR(50),
    region VARCHAR(50),
    special_price DECIMAL(10,2),
    discount_percent DECIMAL(5,2),
    valid_from DATE,
    valid_to DATE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- ==========================================
-- TABELAS DE ORÇAMENTOS
-- ==========================================

-- Cabeçalho dos orçamentos
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY,
    budget_number VARCHAR(50) UNIQUE,
    client_name VARCHAR(200),
    client_email VARCHAR(100),
    client_phone VARCHAR(50),
    salesperson VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until DATE
);

-- Especificações da piscina para cada orçamento
CREATE TABLE budget_pool_specs (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER NOT NULL,
    length DECIMAL(8,2) NOT NULL,
    width DECIMAL(8,2) NOT NULL,
    depth_min DECIMAL(8,2) NOT NULL,
    depth_max DECIMAL(8,2) NOT NULL,
    depth_avg DECIMAL(8,2),
    volume DECIMAL(10,2),
    m3_per_hour DECIMAL(10,2),
    access_level VARCHAR(50),
    has_excavation BOOLEAN,
    shape VARCHAR(50),
    pool_type VARCHAR(50),
    coating_type VARCHAR(50),
    has_domotics BOOLEAN,
    location VARCHAR(50),
    power_type VARCHAR(50),
    calculated_metrics TEXT, -- JSON com todas as métricas
    FOREIGN KEY (budget_id) REFERENCES budgets(id)
);

-- Itens do orçamento
CREATE TABLE budget_items (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    is_optional BOOLEAN DEFAULT FALSE,
    selection_reason TEXT,
    item_order INTEGER DEFAULT 0,
    FOREIGN KEY (budget_id) REFERENCES budgets(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Totais por família no orçamento
CREATE TABLE budget_family_totals (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER NOT NULL,
    family_id INTEGER NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    multiplier DECIMAL(5,3) DEFAULT 1.0,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budgets(id),
    FOREIGN KEY (family_id) REFERENCES product_families(id)
);

-- ==========================================
-- DADOS BÁSICOS INICIAIS
-- ==========================================

-- Inserir famílias de produtos
INSERT INTO product_families (name, description, display_order) VALUES
('Filtração', 'Sistemas de filtração da água', 1),
('Recirculação e Iluminação', 'Sistemas de circulação', 2),
('Tratamento da Água', 'Sistemas de tratamento químico', 7),
('Revestimento', 'Revestimentos e acabamentos', 8);

-- Inserir categorias de filtração
INSERT INTO product_categories (family_id, name, display_order) VALUES
(1, 'Filtros de Areia', 1),
(1, 'Filtros de Cartucho', 2),
(1, 'Válvulas Seletoras', 3),
(1, 'Bomba de Filtração', 4),
(1, 'Vidros e Visores', 5),
(1, 'Quadros Elétricos', 6);

-- Inserir tipos de atributos
INSERT INTO attribute_types (name, data_type, unit, description) VALUES
('Capacidade', 'numeric', 'm3/h', 'Capacidade de filtração em metros cúbicos por hora'),
('Voltagem', 'text', 'V', 'Voltagem de operação'),
('Potência', 'numeric', 'HP', 'Potência do motor'),
('Diâmetro', 'numeric', 'mm', 'Diâmetro do equipamento'),
('Material', 'text', '', 'Material de construção'),
('Tipo de Filtro', 'select', '', 'Tipo de meio filtrante'),
('Localização', 'select', '', 'Local de instalação recomendado'),
('Automação', 'boolean', '', 'Suporte à automação'),
('Fase', 'select', '', 'Tipo de alimentação elétrica');

-- Inserir multiplicadores padrão
INSERT INTO price_multipliers (name, condition_type, condition_value, multiplier, applies_to) VALUES
('Acesso Fácil', 'access_level', 'facil', 1.0, 'all'),
('Acesso Médio', 'access_level', 'medio', 1.15, 'all'),
('Acesso Difícil', 'access_level', 'dificil', 1.30, 'all'),
('Sem Escavação', 'excavation', 'false', 1.0, 'all'),
('Com Escavação', 'excavation', 'true', 1.20, 'all'),
('Forma Standard', 'shape', 'standard', 1.0, 'all'),
('Forma Especial', 'shape', 'especial', 1.25, 'all'),
('Sem Domótica', 'domotics', 'false', 1.0, 'all'),
('Com Domótica', 'domotics', 'true', 1.10, 'all');
