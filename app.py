from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, flash
# Ensure template/static paths work when running from a PyInstaller onefile bundle
from calculator import PoolCalculator
from advanced_product_selector import AdvancedProductSelector
from database_manager import DatabaseManager
from budget_cache import budget_cache
import os
import sys
import json

# Resolve base path: if running from PyInstaller bundle, resources are unpacked to sys._MEIPASS
BASE_PATH = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
TEMPLATE_FOLDER = os.path.join(BASE_PATH, 'templates') if os.path.exists(os.path.join(BASE_PATH, 'templates')) else os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
STATIC_FOLDER = os.path.join(BASE_PATH, 'static') if os.path.exists(os.path.join(BASE_PATH, 'static')) else os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
# Chave secreta fixa para garantir consistência no executável
app.secret_key = 'orcamento-piscinas-2025-secret-key-fixed'

# Filtro personalizado para nomes das famílias em português
@app.template_filter('family_display_name')
def family_display_name(family_name):
    """Converte nomes técnicos das famílias para nomes adequados em português"""
    family_display_names = {
        'filtracao': 'Filtração',
        'recirculacao_iluminacao': 'Recirculação e Iluminação',
        'tratamento_agua': 'Tratamento de Água',
        'revestimento': 'Revestimento',
        'aquecimento': 'Aquecimento',
        'construcao': 'Construção da Piscina'
    }
    return family_display_names.get(family_name, family_name.title())

# Inicializar componentes
calculator = PoolCalculator()
product_selector = AdvancedProductSelector()
db_manager = DatabaseManager()

def get_current_budget():
    """Obtém o orçamento atual da sessão ou cache"""
    # Primeiro, tentar obter da sessão (para orçamentos pequenos)
    if 'current_budget' in session:
        return session['current_budget']
    
    # Se não estiver na sessão, tentar cache
    if 'budget_cache_id' in session:
        cached_budget = budget_cache.get_budget(session['budget_cache_id'])
        if cached_budget:
            return cached_budget
    
    return {}

def save_current_budget(budget):
    """Salva o orçamento na sessão ou cache dependendo do tamanho"""
    # Calcular tamanho do orçamento
    budget_json = json.dumps(budget)
    budget_size = len(budget_json.encode('utf-8'))
    
    # Se for menor que 3KB, manter na sessão
    if budget_size < 3000:
        session['current_budget'] = budget
        # Limpar cache se existir
        if 'budget_cache_id' in session:
            del session['budget_cache_id']
    else:
        # Orçamento grande, usar cache
        if 'budget_cache_id' in session:
            # Atualizar cache existente
            budget_cache.update_budget(session['budget_cache_id'], budget)
        else:
            # Criar novo cache
            cache_id = budget_cache.store_budget(budget)
            session['budget_cache_id'] = cache_id
        
        # Remover da sessão para economizar espaço
        if 'current_budget' in session:
            del session['current_budget']

def calculate_and_update_totals(budget):
    """Calcula e atualiza os totais das famílias com valores base, multiplicador e IVA"""
    
    if 'family_totals' not in budget:
        budget['family_totals'] = {}
    if 'family_totals_base' not in budget:
        budget['family_totals_base'] = {}
    if 'total_price' not in budget:
        budget['total_price'] = 0
    if 'subtotal_base' not in budget:
        budget['subtotal_base'] = 0
    # Novos campos para IVA
    if 'iva_rate' not in budget:
        budget['iva_rate'] = 0.23  # IVA padrão 23% em Portugal
    if 'subtotal_with_margin' not in budget:
        budget['subtotal_with_margin'] = 0
    if 'iva_amount' not in budget:
        budget['iva_amount'] = 0
    if 'total_with_iva' not in budget:
        budget['total_with_iva'] = 0
    
    # Verificar estrutura do orçamento - pode ser 'selected_products' ou 'families'
    products_data = budget.get('selected_products', budget.get('families', {}))
        
    # Calcular total por família
    for family, products in products_data.items():
        family_total = 0
        
        for product_id, product in products.items():
            # Contar apenas produtos INCLUÍDOS (excluir alternativos e opcionais)
            quantity = product.get('quantity', 0)
            price = product.get('price', 0)
            item_type = product.get('item_type', 'incluido')
            
            # Apenas produtos incluídos contam no orçamento
            if quantity > 0 and item_type == 'incluido':
                subtotal = price * quantity
                family_total += subtotal
        
        if family_total > 0:
            # Armazenar valor base (sem multiplicador)
            budget['family_totals_base'][family] = round(family_total, 2)
            
            # Aplicar multiplicador para cálculos internos
            multiplier = budget['pool_info'].get('multiplier', 1.0)
            family_total_with_multiplier = family_total * multiplier
            budget['family_totals'][family] = round(family_total_with_multiplier, 2)
        else:
            # Se total for zero, manter os valores zerados
            budget['family_totals_base'][family] = 0
            budget['family_totals'][family] = 0
    
    # Calcular totais gerais
    budget['subtotal_base'] = sum(budget['family_totals_base'].values())
    budget['subtotal_with_margin_only'] = sum(budget['family_totals'].values())  # Só equipamentos com margem
    
    # Adicionar custos de transporte de areia (se existirem)
    transport_costs = budget.get('pool_info', {}).get('transport_costs', {})
    transport_cost = transport_costs.get('custo_total', 0) if transport_costs else 0
    
    # Total com margem E transporte
    budget['subtotal_with_margin'] = budget['subtotal_with_margin_only'] + transport_cost
    
    # Calcular IVA sobre o valor com margem (incluindo transporte)
    budget['iva_amount'] = budget['subtotal_with_margin'] * budget['iva_rate']
    
    # Total final com IVA
    budget['total_with_iva'] = budget['subtotal_with_margin'] + budget['iva_amount']
    
    # Manter total_price para compatibilidade (valor com margem sem IVA)
    budget['total_price'] = budget['subtotal_with_margin']

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir arquivos estáticos incluindo o PDF template"""
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/')
def index():
    """Página inicial - Landing Page Limpa"""
    return render_template('index_clean.html')

@app.route('/client_data')
def client_data():
    """Formulário de dados do cliente - DESIGN LIMPO"""
    return render_template('client_data_clean.html')

@app.route('/save_client_data', methods=['POST'])
def save_client_data():
    """Salvar dados do cliente na sessão"""
    try:
        # Suporta tanto JSON quanto form data
        if request.is_json:
            client_data = request.get_json()
            session['client_data'] = client_data
            return jsonify({'success': True})
        else:
            client_data = request.form.to_dict()
            session['client_data'] = client_data
            # Para formulários HTML, redireciona para a próxima página
            return redirect(url_for('questionnaire'))
            
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        else:
            # Para formulários HTML, redireciona de volta com erro
            flash(f'Erro ao salvar dados: {str(e)}', 'error')
            return redirect(url_for('client_data'))

@app.route('/questionnaire')
def questionnaire():
    """Página do questionário interativo limpo"""
    # Verificar se é uma modificação (vindo do botão Modificar)
    is_modify = request.args.get('modify') == 'true'
    
    # Se for modificação, enviar dados existentes para pré-preenchimento
    existing_data = None
    if is_modify and 'pool_info' in session:
        existing_data = {
            'pool_info': session.get('pool_info', {}),
            'client_info': session.get('client_info', {}),
            'is_modify': True
        }
    
    return render_template('questionnaire_clean.html', existing_data=existing_data)

@app.route('/calculate', methods=['POST'])
def calculate_metrics():
    """Calcula métricas da piscina baseado nas dimensões"""
    try:
        # Suporta tanto JSON quanto form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Converte strings para float quando necessário
            for key in ['comprimento', 'largura', 'prof_min', 'prof_max']:
                if key in data:
                    try:
                        data[key] = str(float(data[key]))  # Converte para float e depois para string
                    except (ValueError, TypeError):
                        data[key] = '0'
        
        # Extrair dimensões
        comprimento = float(data.get('comprimento', 0))
        largura = float(data.get('largura', 0))
        prof_min = float(data.get('prof_min', 0))
        prof_max = float(data.get('prof_max', 0))
        
        # Calcular métricas usando as fórmulas fornecidas
        metrics = calculator.calculate_all_metrics(
            comprimento, largura, prof_min, prof_max
        )
        
        # Armazenar na sessão
        session['pool_metrics'] = metrics
        session['pool_dimensions'] = {
            'comprimento': comprimento,
            'largura': largura,
            'prof_min': prof_min,
            'prof_max': prof_max
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/generate_budget', methods=['POST'])
def generate_budget():
    """Gera orçamento baseado nas respostas do questionário"""
    try:
        print(f"DEBUG: Iniciando generate_budget")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request is_json: {request.is_json}")
        print(f"DEBUG: Request content_type: {request.content_type}")
        
        # Suporta tanto JSON quanto form data
        if request.is_json:
            data = request.get_json()
            print(f"DEBUG: Dados JSON recebidos: {data}")
        else:
            data = request.form.to_dict()
            print(f"DEBUG: Dados FORM recebidos: {data}")
        
        print(f"DEBUG: Processando dados...")
        
        # Extrair respostas do questionário com conversão segura
        answers = {
            'acesso': data.get('acesso'),
            'escavacao': str(data.get('escavacao', 'false')).lower() == 'true',
            'forma': data.get('forma'),
            'tipo_piscina': data.get('tipo_piscina'),
            'revestimento': data.get('revestimento'),
            'domotica': str(data.get('domotica', 'false')).lower() == 'true',
            'localizacao': data.get('localizacao'),
            'luz': data.get('luz'),
            # CAMPOS NOVOS
            'tratamento_agua': data.get('tratamento_agua'),
            'tipo_construcao': data.get('tipo_construcao'),
            'cobertura': data.get('cobertura'),
            'tipo_cobertura_laminas': data.get('tipo_cobertura_laminas'),
            'casa_maquinas_abaixo': data.get('casa_maquinas_abaixo'),
            'tipo_luzes': data.get('tipo_luzes'),
            # ZONA DE PRAIA E ESCADAS
            'zona_praia': data.get('zona_praia'),
            'zona_praia_largura': float(data.get('zona_praia_largura', 0)) if data.get('zona_praia_largura') else 0,
            'zona_praia_comprimento': float(data.get('largura', 0)) if data.get('zona_praia') == 'sim' else 0,  # Comprimento = largura da piscina
            'escadas': data.get('escadas'),
            'escadas_largura': float(data.get('escadas_largura', 0)) if data.get('escadas_largura') else 0
        }
        
        print(f"DEBUG: Answers processadas: {answers}")
        
        # Validar campos obrigatórios
        required_fields = ['acesso', 'forma', 'tipo_piscina', 'revestimento', 'localizacao', 'luz']
        missing_fields = [field for field in required_fields if not answers.get(field)]
        
        if missing_fields:
            error_msg = f"Campos obrigatórios em falta: {', '.join(missing_fields)}"
            print(f"DEBUG: ERRO - {error_msg}")
            raise ValueError(error_msg)
        
        print(f"DEBUG: Validação de campos passou")
        
        # Extrair e calcular dimensões/métricas com validação
        try:
            dimensions = {
                'comprimento': float(data.get('comprimento', 0)),
                'largura': float(data.get('largura', 0)),
                'prof_min': float(data.get('prof_min', 0)),
                'prof_max': float(data.get('prof_max', 0))
            }
            
            print(f"DEBUG: Dimensions extraídas: {dimensions}")
            
            # Validar dimensões mínimas
            if dimensions['comprimento'] <= 0 or dimensions['largura'] <= 0:
                raise ValueError("Comprimento e largura devem ser maiores que zero")
            
            if dimensions['prof_min'] <= 0 or dimensions['prof_max'] <= 0:
                raise ValueError("Profundidades devem ser maiores que zero")
            
        except (ValueError, TypeError) as e:
            error_msg = f"Erro nas dimensões: {str(e)}"
            print(f"DEBUG: ERRO - {error_msg}")
            raise ValueError(error_msg)
        
        # Calcular todas as métricas usando o calculator
        calc = PoolCalculator()
        metrics = calc.calculate_all_metrics(
            dimensions['comprimento'],
            dimensions['largura'], 
            dimensions['prof_min'],
            dimensions['prof_max']
        )
        
        # Verificar se temos valores calculados do frontend e usá-los se disponíveis
        if 'm3_massa' in data and data['m3_massa']:
            metrics['m3_massa'] = float(data['m3_massa'])
        if 'm2_fundo' in data and data['m2_fundo']:
            metrics['m2_fundo'] = float(data['m2_fundo'])
        if 'm2_paredes' in data and data['m2_paredes']:
            metrics['m2_paredes'] = float(data['m2_paredes'])
        if 'm2_tela' in data and data['m2_tela']:
            metrics['m2_tela'] = float(data['m2_tela'])
        if 'ml_bordadura' in data and data['ml_bordadura']:
            metrics['ml_bordadura'] = float(data['ml_bordadura'])
        if 'rolos_tl' in data and data['rolos_tl']:
            metrics['rolos_tl'] = int(data['rolos_tl'])
        if 'rolos_3d' in data and data['rolos_3d']:
            metrics['rolos_3d'] = int(data['rolos_3d'])
        
        # Salvar na sessão
        session['pool_metrics'] = metrics
        session['pool_dimensions'] = dimensions
        
        # Gerar orçamento
        print(f"DEBUG: Iniciando geração de orçamento...")
        print(f"DEBUG: Answers: {answers}")
        print(f"DEBUG: Metrics: {metrics}")
        print(f"DEBUG: Dimensions: {dimensions}")
        
        budget = product_selector.generate_budget(answers, metrics, dimensions)
        
        print(f"DEBUG: Orçamento gerado: {budget is not None}")
        if budget:
            print(f"DEBUG: Families no budget: {list(budget.get('families', {}).keys())}")
            print(f"DEBUG: Total price: {budget.get('total_price', 0)}")
        
        # Armazenar orçamento na sessão usando cache inteligente
        save_current_budget(budget)
        print(f"DEBUG: Budget salvo (cache inteligente)")
        
        # Calcular totais base e com multiplicador
        if budget:
            calculate_and_update_totals(budget)
            save_current_budget(budget)
            print(f"DEBUG: Totais calculados e atualizados")
        
        # Resposta baseada no tipo de requisição
        if request.is_json:
            print(f"DEBUG: Retornando resposta JSON")
            return jsonify({
                'success': True,
                'budget': budget
            })
        else:
            # Para formulários HTML, redireciona para a página de orçamento
            print(f"DEBUG: Redirecionando para /budget")
            return redirect(url_for('view_budget'))
        
    except Exception as e:
        print(f"DEBUG: ERRO em generate_budget: {str(e)}")
        print(f"DEBUG: Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Stack trace: {traceback.format_exc()}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        else:
            # Para formulários HTML, redireciona de volta com erro
            flash(f'Erro ao gerar orçamento: {str(e)}', 'error')
            print(f"DEBUG: Redirecionando para /questionnaire devido a erro")
            return redirect(url_for('questionnaire'))

@app.route('/budget')
def view_budget():
    """Visualizar e editar orçamento gerado"""
    
    budget = get_current_budget()
    if not budget:
        return redirect('/')
    
    # Obter dados do cliente da sessão
    client_data = session.get('client_data', {})
    
    # Garantir que client_info e pool_info estão definidos
    if 'client_info' not in budget:
        budget['client_info'] = client_data
    if 'pool_info' not in budget:
        budget['pool_info'] = session.get('pool_info', {})
    if 'family_totals' not in budget:
        budget['family_totals'] = {}
    if 'total_price' not in budget:
        budget['total_price'] = 0
    
    # Garantir que os novos campos de totais estão inicializados
    calculate_and_update_totals(budget)
    
    # Limpar valores None/undefined que podem causar erro de serialização
    def clean_undefined_values(obj):
        if isinstance(obj, dict):
            return {k: clean_undefined_values(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [clean_undefined_values(item) for item in obj if item is not None]
        else:
            return obj
    
    budget = clean_undefined_values(budget)
    client_data = clean_undefined_values(client_data)
    
    return render_template('budget_clean.html', budget=budget, client_data=client_data)

@app.route('/update_budget', methods=['POST'])
def update_budget():
    """Atualizar itens do orçamento manualmente"""
    try:
        # Suporta tanto JSON quanto form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        budget = session.get('current_budget', {})
        
        # Atualizar item específico
        family = data.get('family')
        item_id = data.get('item_id')
        quantity_value = data.get('quantity', 1)
        
        # Garantir que quantity seja um número válido
        if quantity_value is None or quantity_value == '':
            quantity_value = 1
        
        try:
            new_quantity = int(quantity_value)
        except (ValueError, TypeError):
            new_quantity = 1
        
        if family in budget['families'] and item_id in budget['families'][family]:
            budget['families'][family][item_id]['quantity'] = new_quantity
            
            # Recalcular total da família com multiplicador
            family_total = sum(
                item['price'] * item['quantity'] 
                for item in budget['families'][family].values()
                if item.get('item_type', 'incluido') == 'incluido'
            )
        # Recalcular totais usando a nova função
        calculate_and_update_totals(budget)
        
        session['current_budget'] = budget
        
        return jsonify({
            'success': True,
            'new_total': budget['total_price']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/switch_product', methods=['POST'])
def switch_product():
    """Trocar produto incluído por opcional da mesma família"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = session.get('current_budget', {})
        
        family = data.get('family')
        target_product_id = data.get('item_id')
        
        if family not in budget['families']:
            return jsonify({'success': False, 'error': 'Família não encontrada'}), 400
        
        family_products = budget['families'][family]
        
        # Encontrar o produto opcional que quer virar incluído
        target_product = family_products.get(target_product_id)
        if not target_product or target_product.get('item_type') != 'alternativo':
            return jsonify({'success': False, 'error': 'Produto alternativo não encontrado'}), 400
        
        # Identificar qual produto específico este alternativo deve substituir
        alternative_to = target_product.get('alternative_to')
        
        if alternative_to and alternative_to in family_products:
            # Trocar especificamente com o produto principal definido
            main_product = family_products[alternative_to]
            
            # Fazer a troca apenas entre estes dois produtos
            if main_product.get('item_type') == 'incluido':
                # Decidir quantidade preservada: preferir a quantidade que a alternativa já tinha
                # caso exista; senão copiar a quantidade do produto principal; como fallback usar 1.
                try:
                    alt_qty = int(target_product.get('quantity', 0) or 0)
                except (ValueError, TypeError):
                    alt_qty = 0

                try:
                    main_qty = int(main_product.get('quantity', 0) or 0)
                except (ValueError, TypeError):
                    main_qty = 0

                preserved_qty = alt_qty if alt_qty > 0 else (main_qty if main_qty > 0 else 1)

                # Produto principal vira alternativo (manter sua quantidade para visualização)
                main_product['item_type'] = 'alternativo'
                # manter quantidade existente para que o alternativo mostre preço/quantidade
                main_product['quantity'] = main_qty
                main_product['alternative_to'] = target_product_id  # CRUCIAL: definir a nova relação
                # Limpar nome e adicionar (ALTERNATIVO)
                original_name = main_product['name'].replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '')
                main_product['name'] = original_name + ' (ALTERNATIVO)'

                # Produto alternativo vira incluído (preservando quantidade apropriada)
                target_product['item_type'] = 'incluido'
                target_product['quantity'] = preserved_qty
                # Remover a relação alternative_to (agora ele é o principal)
                if 'alternative_to' in target_product:
                    del target_product['alternative_to']
                # Limpar nome
                original_name = target_product['name'].replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '')
                target_product['name'] = original_name
            else:
                return jsonify({'success': False, 'error': 'Produto principal não está incluído'}), 400
        else:
            # Fallback: procurar produto incluído do mesmo tipo/categoria
            included_products = [
                (prod_id, prod) for prod_id, prod in family_products.items() 
                if prod.get('item_type') == 'incluido'
            ]
            
            if not included_products:
                return jsonify({'success': False, 'error': 'Nenhum produto incluído encontrado para trocar'}), 400
            
            # Identificar o tipo do produto alternativo para trocar com produto similar
            target_name = target_product.get('name', '').lower()
            
            # Encontrar produto incluído do mesmo tipo
            similar_product = None
            
            # Definir categorias por palavras-chave no nome
            if any(keyword in target_name for keyword in ['válvula', 'valvula']):
                # Procurar por outras válvulas
                for prod_id, prod in included_products:
                    prod_name = prod.get('name', '').lower()
                    if any(keyword in prod_name for keyword in ['válvula', 'valvula']):
                        similar_product = (prod_id, prod)
                        break
            elif any(keyword in target_name for keyword in ['filtro', 'filter']):
                # Procurar por outros filtros
                for prod_id, prod in included_products:
                    prod_name = prod.get('name', '').lower()
                    if any(keyword in prod_name for keyword in ['filtro', 'filter']):
                        similar_product = (prod_id, prod)
                        break
            elif any(keyword in target_name for keyword in ['bomba', 'pump']):
                # Procurar por outras bombas
                for prod_id, prod in included_products:
                    prod_name = prod.get('name', '').lower()
                    if any(keyword in prod_name for keyword in ['bomba', 'pump']):
                        similar_product = (prod_id, prod)
                        break
            elif any(keyword in target_name for keyword in ['quadro', 'painel', 'controle']):
                # Procurar por outros quadros/painéis
                for prod_id, prod in included_products:
                    prod_name = prod.get('name', '').lower()
                    if any(keyword in prod_name for keyword in ['quadro', 'painel', 'controle']):
                        similar_product = (prod_id, prod)
                        break
            
            # Se não encontrou produto similar, pegar o primeiro (fallback do fallback)
            if not similar_product:
                similar_product = included_products[0]
            
            similar_id, similar_prod = similar_product
            
            # Fazer a troca apenas entre estes dois produtos
            # Preservar quantidade adequada: se a alternativa já tinha quantidade (>0), usar essa;
            # senão copiar a quantidade do similar_prod; fallback 1.
            try:
                alt_qty = int(target_product.get('quantity', 0) or 0)
            except (ValueError, TypeError):
                alt_qty = 0

            try:
                similar_qty = int(similar_prod.get('quantity', 0) or 0)
            except (ValueError, TypeError):
                similar_qty = 0

            preserved_qty = alt_qty if alt_qty > 0 else (similar_qty if similar_qty > 0 else 1)

            similar_prod['item_type'] = 'alternativo'
            # Manter a quantidade do produto similar para que o alternativo mostre preço/quantidade
            similar_prod['quantity'] = similar_qty
            similar_prod['alternative_to'] = target_product_id  # CRUCIAL: definir a nova relação
            original_name = similar_prod['name'].replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '')
            similar_prod['name'] = original_name + ' (ALTERNATIVO)'

            # Produto alternativo vira incluído (preservando quantidade apropriada)
            target_product['item_type'] = 'incluido'
            target_product['quantity'] = preserved_qty
            # Remover a relação alternative_to (agora ele é o principal)
            if 'alternative_to' in target_product:
                del target_product['alternative_to']
            original_name = target_product['name'].replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '')
            target_product['name'] = original_name
        
        # Recalcular totais com multiplicador
        family_total = sum(
            item['price'] * item['quantity'] 
            for item in family_products.values()
            if item.get('item_type') == 'incluido'
        )
        
        # Recalcular totais usando a nova função
        calculate_and_update_totals(budget)
        
        session['current_budget'] = budget
        
        return jsonify({
            'success': True,
            'new_total': budget['total_price']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    """Atualizar quantidade de um produto"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = session.get('current_budget', {})
        
        product_id = data.get('product_id')
        quantity_value = data.get('quantity', 1)
        
        # Garantir que quantity seja um número válido
        if quantity_value is None or quantity_value == '':
            quantity_value = 0
        
        try:
            new_quantity = float(quantity_value)  # Usar float para aceitar decimais
        except (ValueError, TypeError):
            new_quantity = 0
        
        # Encontrar o produto em todas as famílias
        product_found = False
        for family_name, family_products in budget.get('families', {}).items():
            if product_id in family_products:
                family_products[product_id]['quantity'] = max(0, new_quantity)  # Permitir quantidade 0 e decimais
                product_found = True
                break
        
        if product_found:
            # Recalcular totais da família
            for family_name, family_products in budget['families'].items():
                family_total = sum(
                    item['price'] * item['quantity'] 
                    for item in family_products.values() 
                    if item['quantity'] > 0
                )
                
                # Recalcular totais usando a nova função
                calculate_and_update_totals(budget)

            # Atualizar valores agregados
            budget['total_price'] = sum(budget['family_totals'].values())
            # Garantir que cálculos de IVA e subtotais estejam atualizados
            # calculate_and_update_totals já atualiza subtotal_with_margin e total_with_iva
            session['current_budget'] = budget
            
            # Preparar payload com totais detalhados para atualização dinâmica no frontend
            response_payload = {
                'success': True,
                'total_price': budget.get('total_price', 0),
                'subtotal_with_margin': budget.get('subtotal_with_margin', 0),
                'total_with_iva': budget.get('total_with_iva', 0),
                'iva_amount': budget.get('iva_amount', 0),
                'family_totals': budget.get('family_totals', {}),
                'family_totals_base': budget.get('family_totals_base', {})
            }

            return jsonify(response_payload)
        else:
            return jsonify({
                'success': False,
                'error': 'Produto não encontrado'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/update_product_name', methods=['POST'])
def update_product_name():
    """Atualizar nome de um produto editável"""
    try:
        data = request.get_json()
        budget = session.get('current_budget', {})
        
        product_id = data.get('product_id')
        new_name = data.get('name', '').strip()
        
        if not product_id or not new_name:
            return jsonify({
                'success': False,
                'error': 'ID do produto e nome são obrigatórios'
            }), 400
        
        # Encontrar o produto em todas as famílias
        product_found = False
        for family_name, family_products in budget.get('families', {}).items():
            if product_id in family_products:
                # Verificar se o produto permite edição de nome
                if family_products[product_id].get('editable_name', False):
                    family_products[product_id]['name'] = new_name
                    product_found = True
                    break
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Este produto não permite edição de nome'
                    }), 400
        
        if product_found:
            session['current_budget'] = budget
            return jsonify({'success': True})
        else:
            return jsonify({
                'success': False,
                'error': 'Produto não encontrado'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/update_product_price', methods=['POST'])
def update_product_price():
    """Atualizar preço de um produto editável"""
    try:
        data = request.get_json()
        budget = session.get('current_budget', {})
        
        product_id = data.get('product_id')
        new_price = data.get('price')
        
        if not product_id or new_price is None:
            return jsonify({
                'success': False,
                'error': 'ID do produto e preço são obrigatórios'
            }), 400
        
        try:
            new_price = float(new_price)
            if new_price < 0:
                raise ValueError("Preço não pode ser negativo")
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Preço deve ser um número válido e não negativo'
            }), 400
        
        # Encontrar o produto em todas as famílias
        product_found = False
        for family_name, family_products in budget.get('families', {}).items():
            if product_id in family_products:
                # Verificar se o produto permite edição de preço
                if family_products[product_id].get('editable_price', False):
                    family_products[product_id]['price'] = new_price
                    product_found = True
                    
                    # Recalcular totais
                    calculate_and_update_totals(budget)
                    budget['total_price'] = sum(budget['family_totals'].values())
                    break
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Este produto não permite edição de preço'
                    }), 400
        
        if product_found:
            session['current_budget'] = budget
            return jsonify({
                'success': True,
                'new_total': budget['total_price']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Produto não encontrado'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/recalculate_budget', methods=['POST'])
def recalculate_budget():
    """Recalcular orçamento com novos dados de medidas e respostas do questionário"""
    try:
        data = request.get_json()
        # Obter dados do cliente (mantemos compatibilidade com as rotas existentes)
        client_data = session.get('client_data', {})
        if not client_data:
            return jsonify({'success': False, 'error': 'Dados do cliente não encontrados'}), 400

        # Construir pool_info a partir do payload
        pool_info = {
            'comprimento': float(data.get('comprimento', 0)),
            'largura': float(data.get('largura', 0)),
            'prof_min': float(data.get('prof_min', 0)),
            'prof_max': float(data.get('prof_max', 0)),
            'answers': data.get('answers', {})
        }

        # Calcular métricas
        metrics = calculator.calculate_all_metrics(
            pool_info['comprimento'],
            pool_info['largura'],
            pool_info['prof_min'],
            pool_info['prof_max']
        )

        pool_info.update(metrics)

        answers = pool_info.get('answers', {})
        dimensions = {
            'comprimento': pool_info['comprimento'],
            'largura': pool_info['largura'],
            'prof_min': pool_info['prof_min'],
            'prof_max': pool_info['prof_max']
        }

        # Gerar novo orçamento usando o product_selector
        budget = product_selector.generate_budget(answers, metrics, dimensions)

        # Salvar usando cache inteligente para evitar cookie overflow
        save_current_budget(budget)
        # Guardar apenas métricas e dimensões curtas na sessão para rápido acesso
        session['pool_metrics'] = metrics
        session['pool_dimensions'] = dimensions

        return jsonify({'success': True, 'message': 'Orçamento recalculado com sucesso'})
        
    except Exception as e:
        print(f"Erro ao recalcular orçamento: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/get_current_answers', methods=['GET'])
def get_current_answers():
    """Retorna as respostas atuais do questionário"""
    try:
        budget = get_current_budget()
        pool_info = budget.get('pool_info', {})

        # Tentar obter answers de diferentes fontes
        answers = pool_info.get('answers', {})
        if not answers:
            # Fallback para campos individuais se answers não existir
            answers = {
                'acesso': pool_info.get('acesso', 'facil'),
                'escavacao': pool_info.get('escavacao', 'mecanica'),
                'forma': pool_info.get('forma', 'retangular'),
                'tipo_piscina': pool_info.get('tipo_piscina', 'skimmer'),
                'revestimento': pool_info.get('revestimento', 'vinil'),
                'domotica': pool_info.get('domotica', 'nao'),
                'localizacao': pool_info.get('localizacao', 'exterior'),
                'luz': pool_info.get('luz', 'led'),
                'tratamento_agua': pool_info.get('tratamento_agua', 'cloro_manual'),
                'tipo_construcao': pool_info.get('tipo_construcao', 'nova'),
                'cobertura': pool_info.get('cobertura', 'nao'),
                'tipo_cobertura_laminas': pool_info.get('tipo_cobertura_laminas', ''),
                'casa_maquinas_abaixo': pool_info.get('casa_maquinas_abaixo', 'nao'),
                'casa_maquinas_desc': pool_info.get('casa_maquinas_desc', ''),
                'tipo_luzes': pool_info.get('tipo_luzes', 'branco_frio'),
                # Zona de praia e escadas
                'zona_praia': pool_info.get('zona_praia', 'nao'),
                'zona_praia_largura': pool_info.get('zona_praia_largura', 0),
                'zona_praia_comprimento': pool_info.get('zona_praia_comprimento', 0),
                'escadas': pool_info.get('escadas', 'nao'),
                'escadas_largura': pool_info.get('escadas_largura', 0)
            }
        
        return jsonify({
            'success': True,
            'answers': answers
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'answers': {
                'acesso': 'facil',
                'escavacao': 'mecanica',
                'forma': 'retangular',
                'tipo_piscina': 'skimmer',
                'revestimento': 'vinil',
                'domotica': 'nao',
                'localizacao': 'exterior',
                'luz': 'led',
                'tratamento_agua': 'cloro_manual'
            }
        })

@app.route('/toggle_optional', methods=['POST'])
def toggle_optional():
    """Alternar produto opcional entre incluído e não incluído"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = session.get('current_budget', {})

        product_id = data.get('product_id')
        include = data.get('include', True)

        # Encontrar o produto em todas as famílias
        product_found = False
        for family_name, family_products in budget.get('families', {}).items():
            if product_id in family_products:
                product = family_products[product_id]
                # Aceitar produtos opcionais ou produtos que eram opcionais (incluídos via toggle)
                current_type = product.get('item_type')
                is_toggleable = (current_type == 'opcional' or 
                               (current_type == 'incluido' and product.get('was_optional', False)))

                if is_toggleable or current_type == 'opcional':
                    if include and current_type == 'opcional':
                        # Quando incluir: produto vira "incluído" e quantidade = 1
                        product['item_type'] = 'incluido'
                        product['quantity'] = max(1, product.get('quantity', 1))
                        product['was_optional'] = True  # Marcar que era opcional
                        # Limpar nome (remover sufixos opcionais se houver)
                        original_name = product['name'].replace(' (OPCIONAL)', '').replace(' (ALTERNATIVO)', '')
                        product['name'] = original_name
                    elif not include and product.get('was_optional', False):
                        # Quando remover: produto volta a ser "opcional" e quantidade = 0
                        product['item_type'] = 'opcional'
                        product['quantity'] = 0
                        product['was_optional'] = False
                    elif not include and current_type == 'opcional':
                        # Produto opcional sendo "desincluído"
                        product['quantity'] = 0
                    product_found = True
                    break

        if product_found:
            # Recalcular totais da família excluindo alternativos
            for family_name, family_products in budget['families'].items():
                family_total = sum(
                    item['price'] * item['quantity'] 
                    for item in family_products.values() 
                    if item['quantity'] > 0 and item.get('item_type', 'incluido') in ['incluido', 'opcional']
                )

                # Recalcular totais usando a nova função
                calculate_and_update_totals(budget)

            budget['total_price'] = sum(budget['family_totals'].values())
            session['current_budget'] = budget

            return jsonify({
                'success': True,
                'new_total': budget['total_price']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Produto opcional não encontrado'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/update_project_configuration', methods=['POST'])
def update_project_configuration():
    """Recebe atualização da configuração do projeto a partir do modal e atualiza o orçamento na sessão"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = get_current_budget()

        if 'pool_info' not in budget:
            budget['pool_info'] = {}
        if 'answers' not in budget['pool_info']:
            budget['pool_info']['answers'] = {}

        answers = budget['pool_info']['answers']

        # Campos esperados (todos os campos do questionário)
        fields = [
            'acesso', 'escavacao', 'forma', 'tipo_piscina', 'revestimento', 'domotica', 
            'localizacao', 'luz', 'tratamento_agua', 'tipo_construcao', 'cobertura', 
            'tipo_cobertura_laminas', 'casa_maquinas_abaixo', 'casa_maquinas_desc', 
            'tipo_luzes', 'zona_praia', 'zona_praia_largura', 'zona_praia_comprimento',
            'escadas', 'escadas_largura'
        ]
        
        for f in fields:
            if f in data:
                # Converter valores numéricos quando necessário
                if f in ['zona_praia_largura', 'zona_praia_comprimento', 'escadas_largura']:
                    try:
                        answers[f] = float(data.get(f, 0)) if data.get(f) else 0
                    except (ValueError, TypeError):
                        answers[f] = 0
                else:
                    answers[f] = data.get(f)

        # Medidas
        dimensions = session.get('pool_dimensions', {})
        try:
            dimensions['comprimento'] = float(data.get('comprimento', dimensions.get('comprimento', 0)) or 0)
            dimensions['largura'] = float(data.get('largura', dimensions.get('largura', 0)) or 0)
            dimensions['prof_min'] = float(data.get('prof_min', dimensions.get('prof_min', 0)) or 0)
            dimensions['prof_max'] = float(data.get('prof_max', dimensions.get('prof_max', 0)) or 0)
        except Exception:
            # keep existing if conversion fails
            pass

        # Salvar de volta
        budget['pool_info']['answers'] = answers
        budget['pool_info']['dimensions'] = dimensions
        session['pool_dimensions'] = dimensions
        # Salvar o orçamento usando cache inteligente
        save_current_budget(budget)

        # Recalcular orcamento se a função estiver disponível
        try:
            calculate_and_update_totals(budget)
            save_current_budget(budget)
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Configuração atualizada'})
    except Exception as e:
        print(f"ERROR update_project_configuration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/update_item_type', methods=['POST'])
def update_item_type():
    """Alterar tipo do item (incluído/opcional/oferta)"""
    try:
        # Suporta tanto JSON quanto form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        budget = session.get('current_budget', {})
        
        family = data.get('family')
        item_id = data.get('item_id')
        new_type = data.get('item_type', 'incluido')
        
        if family in budget['families'] and item_id in budget['families'][family]:
            # Atualizar tipo do item
            budget['families'][family][item_id]['item_type'] = new_type
            
            # Se mudou para opcional ou oferta, zerar quantidade
            if new_type in ['opcional', 'oferta']:
                budget['families'][family][item_id]['quantity'] = 0
            elif new_type == 'incluido' and budget['families'][family][item_id]['quantity'] == 0:
                # Se mudou para incluído e estava zerado, colocar 1
                budget['families'][family][item_id]['quantity'] = 1
            
            # Recalcular total da família com multiplicador
            family_total = sum(
                item['price'] * item['quantity'] 
                for item in budget['families'][family].values()
                if item.get('item_type', 'incluido') == 'incluido'
            )
            
            # Recalcular totais usando a nova função
            calculate_and_update_totals(budget)
            
            session['current_budget'] = budget
            
        return jsonify({
            'success': True,
            'new_total': budget['total_price']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/debug_session_size')
def debug_session_size():
    """Debug para verificar tamanho da sessão"""
    import json
    
    session_data = dict(session)
    session_json = json.dumps(session_data)
    size_bytes = len(session_json.encode('utf-8'))
    
    # Calcular tamanho por seção
    sizes = {}
    for key, value in session_data.items():
        key_json = json.dumps({key: value})
        sizes[key] = len(key_json.encode('utf-8'))
    
    return jsonify({
        'total_size_bytes': size_bytes,
        'size_limit': 4093,
        'over_limit': size_bytes > 4093,
        'sections': sizes,
        'current_budget_exists': 'current_budget' in session,
        'families_count': len(session.get('current_budget', {}).get('families', {}))
    })

@app.route('/get_session_data')
def get_session_data():
    """Retorna dados da sessão para exportação PDF"""
    try:
        return jsonify({
            'client_data': session.get('client_data', {}),
            'current_budget': get_current_budget(),
            'pool_metrics': session.get('pool_metrics', {}),
            'pool_dimensions': session.get('pool_dimensions', {})
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 400

@app.route('/debug_totals')
def debug_totals():
    """Endpoint de debug para verificar cálculos de totais"""
    try:
        budget = session.get('current_budget', {})
        if not budget:
            return jsonify({'error': 'Nenhum orçamento na sessão'})
        
        debug_info = {
            'family_totals_base': budget.get('family_totals_base', {}),
            'family_totals': budget.get('family_totals', {}),
            'subtotal_base': budget.get('subtotal_base', 0),
            'subtotal_with_margin_only': budget.get('subtotal_with_margin_only', 0),
            'subtotal_with_margin': budget.get('subtotal_with_margin', 0),
            'transport_costs': budget.get('pool_info', {}).get('transport_costs', {}),
            'iva_amount': budget.get('iva_amount', 0),
            'total_with_iva': budget.get('total_with_iva', 0),
            'total_price': budget.get('total_price', 0),
            'multiplier': budget.get('pool_info', {}).get('multiplier', 1.0),
            'produtos_incluidos': []
        }
        
        # Listar produtos incluídos para verificar o que está sendo contado
        products_data = budget.get('selected_products', budget.get('families', {}))
        for family, products in products_data.items():
            for product_id, product in products.items():
                if product.get('quantity', 0) > 0 and product.get('item_type') == 'incluido':
                    debug_info['produtos_incluidos'].append({
                        'family': family,
                        'name': product.get('name', ''),
                        'quantity': product.get('quantity', 0),
                        'price': product.get('price', 0),
                        'subtotal': product.get('price', 0) * product.get('quantity', 0)
                    })
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/replace_product', methods=['POST'])
def replace_product():
    """Substitui um produto por outro alternativo"""
    try:
        data = request.get_json()
        family = data.get('family')
        current_product_id = data.get('current_product_id')
        new_product_id = data.get('new_product_id')
        
        print(f"DEBUG replace_product: family={family}, current={current_product_id}, new={new_product_id}")
        
        if not all([family, current_product_id, new_product_id]):
            return jsonify({'success': False, 'error': 'Parâmetros inválidos'})
        
        # Extrair ID real do novo produto
        real_new_id = str(new_product_id)
        if '_' in str(new_product_id):
            parts = str(new_product_id).split('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                real_new_id = parts[1]
        
        # Buscar informações do novo produto — FORÇAR uso do fallback default_data.py
        try:
            from default_data import products as fallback_products, product_categories
        except Exception as ex:
            return jsonify({'success': False, 'error': f'Fallback data not available: {ex}'})

        new_product = next((p for p in fallback_products if str(p.get('id')) == str(real_new_id)), None)
        if not new_product:
            return jsonify({'success': False, 'error': f'Produto não encontrado no fallback com ID {real_new_id}'})

        # Enriquecer com nome de categoria (compatível com uso posterior)
        try:
            cat = next((c for c in product_categories if c.get('id') == new_product.get('category_id')), None)
            new_product = dict(new_product)
            new_product['category_name'] = cat.get('name') if cat else ''
        except Exception:
            new_product = dict(new_product)
            new_product['category_name'] = ''
        
        # Obter orçamento atual da sessão
        current_budget = session.get('current_budget', {})
        if not current_budget:
            return jsonify({'success': False, 'error': 'Orçamento não encontrado na sessão'})
        
        # Encontrar e substituir o produto na família
        if family in current_budget.get('families', {}):
            family_products = current_budget['families'][family]
            
            if current_product_id in family_products:
                # Manter quantidade atual
                current_quantity = family_products[current_product_id]['quantity']
                current_item_type = family_products[current_product_id]['item_type']
                
                # Remover produto atual
                del family_products[current_product_id]
                
                # Criar novo ID no formato correto baseado na categoria
                category_prefixes = {
                    'Filtros de Areia': 'filter',
                    'Filtros de Cartucho': 'filter', 
                    'Bombas': 'pump',
                    'Válvulas': 'valve',
                    'Quadros Elétricos': 'panel'
                }
                
                new_category = new_product.get('category_name', '')
                prefix = category_prefixes.get(new_category, 'product')
                new_key = f"{prefix}_{new_product['id']}"
                
                # Adicionar novo produto
                family_products[new_key] = {
                    'id': new_product['id'],
                    'name': new_product['name'],
                    'price': new_product['base_price'],
                    'quantity': current_quantity,
                    'item_type': current_item_type,  # Manter tipo anterior
                    'unit': new_product.get('unit', 'un'),
                    'reasoning': f'Produto substituído pelo comercial'
                }
                
                # Recalcular total da família excluindo alternativos
                family_total = sum(
                    p['price'] * p['quantity'] for p in family_products.values() 
                    if p['quantity'] > 0 and p.get('item_type', 'incluido') in ['incluido', 'opcional']
                )
                
                # Aplicar multiplicador
                # Recalcular totais usando a nova função
                calculate_and_update_totals(current_budget)
                
                # Salvar na sessão
                session['current_budget'] = current_budget
                
                print(f"DEBUG: Produto substituído com sucesso - {new_product['name']}")
                
                return jsonify({
                    'success': True,
                    'message': f'Produto substituído com sucesso por {new_product["name"]}'
                })
            else:
                return jsonify({'success': False, 'error': 'Produto atual não encontrado no orçamento'})
        else:
            return jsonify({'success': False, 'error': 'Família não encontrada no orçamento'})
        
    except Exception as e:
        print(f"ERRO replace_product: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_alternatives/<family_name>/<current_product_id>')
def get_alternatives(family_name, current_product_id):
    """Busca alternativas disponíveis para um produto específico na base de dados"""
    try:

        print(f"[ALT-DEBUG] family_name recebido: {family_name}")
        import re
        real_product_id = current_product_id
        match = re.search(r'(\d+)$', current_product_id)
        if match:
            real_product_id = match.group(1)
        print(f"[ALT-DEBUG] ID extraído: {current_product_id} -> {real_product_id}")

        family_mapping = {
            'filtracao': 'Filtração',
            'recirculacao': 'Recirculação e Iluminação',
            'recirculacao_iluminacao': 'Recirculação e Iluminação',
            'tratamento': 'Tratamento de Água'
        }
        db_family_name = family_mapping.get(family_name, family_name)
        print(f"[ALT-DEBUG] Família mapeada: {family_name} -> {db_family_name}")

        # Forçar uso do fallback default_data.py como fonte única para alternativas
        try:
            from default_data import products as fallback_products, product_categories, product_families
        except Exception as ex:
            return jsonify({'success': False, 'error': f'Fallback data not available: {ex}'})

        # Encontrar o produto atual no fallback — mas aceitar vários formatos de identificador
        import unicodedata
        def slugify(text: str) -> str:
            if not text:
                return ''
            s = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII')
            s = ''.join(ch for ch in s if ch.isalnum() or ch.isspace() or ch == '_')
            return s.strip().lower().replace(' ', '_')

        current_product = None

        # 1) Se o identificador contém dígitos no final, já tentámos com regex; buscar por id
        if str(real_product_id).isdigit():
            current_product = next((p for p in fallback_products if str(p.get('id')) == str(real_product_id)), None)

        # 2) Se não encontrado, tentar resolver como chave presente no orçamento da sessão
        if not current_product:
            budget = session.get('current_budget', {})
            if budget:
                for fam_key, fam_products in (budget.get('families') or {}).items():
                    if fam_products and str(current_product_id) in fam_products:
                        prod_entry = fam_products.get(str(current_product_id))
                        if prod_entry:
                            pid = prod_entry.get('id') or prod_entry.get('product_id')
                            if pid:
                                current_product = next((p for p in fallback_products if str(p.get('id')) == str(pid)), None)
                                if current_product:
                                    print(f"[ALT-DEBUG] Resolved current_product_id '{current_product_id}' via session family '{fam_key}' -> id {pid}")
                                    break

        # 3) Se ainda não encontrou, tentar matchmaking por slug (nome, código, modelo)
        if not current_product:
            needle = slugify(real_product_id)
            if needle:
                # procurar por name/model/code que slugifique para o mesmo
                for p in fallback_products:
                    if slugify(p.get('name', '') or '') == needle or slugify(p.get('model', '') or '') == needle or slugify(p.get('code', '') or '') == needle:
                        current_product = dict(p)
                        print(f"[ALT-DEBUG] Resolved current_product_id '{current_product_id}' by slug match -> {p.get('id')}")
                        break

        print(f"[ALT-DEBUG] Produto atual (fallback) retornado: {current_product}")
        if not current_product:
            # Fornecer contexto de diagnóstico: possíveis chaves na família da sessão
            poss = []
            budget = session.get('current_budget', {})
            if budget and budget.get('families'):
                for fam_k, fam_p in budget.get('families').items():
                    if isinstance(fam_p, dict):
                        poss.extend(list(fam_p.keys())[:10])
            print(f"[ALT-DEBUG] Produto não encontrado no fallback com ID '{real_product_id}'. Sample keys from session families: {poss}")
            return jsonify({'success': False, 'error': f'Produto não encontrado com ID {real_product_id}'})

        # Mapear família para nomes no fallback (preservar mapeamento anteriormente usado)
        # db_family_name pode ser o nome exibido ou um slug; permitir ambos ao localizar a família
        def fam_slug(s: str) -> str:
            if not s:
                return ''
            import unicodedata
            import re
            t = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').strip().lower()
            t = re.sub(r'[^a-z0-9]+', '_', t).strip('_')
            return t

        fam = None
        for f in product_families:
            if f.get('name') == db_family_name or fam_slug(f.get('name', '')) == str(db_family_name):
                fam = f
                break
        if fam:
            fam_id = fam.get('id')
            family_cat_ids = [c.get('id') for c in product_categories if c.get('family_id') == fam_id]
            all_products = [dict(p) for p in fallback_products if p.get('category_id') in family_cat_ids and p.get('is_active', 1)]
        else:
            # fallback: buscar todos os produtos do fallback
            all_products = [dict(p) for p in fallback_products if p.get('is_active', 1)]

        print(f"[ALT-DEBUG] Produtos retornados por família (fallback {db_family_name}): {len(all_products)}")
        for p in all_products:
            # tentar anexar category_name se possível
            try:
                cat = next((c for c in product_categories if c.get('id') == p.get('category_id')), None)
                p['category_name'] = cat.get('name') if cat else ''
            except Exception:
                p['category_name'] = ''
            print(f"    - {p.get('name')} (ID: {p.get('id')}, categoria: {p.get('category_name')})")

        # Garantir que current_product tem category_name (pode faltar dependendo de como foi resolvido)
        try:
            cur_cat = next((c for c in product_categories if c.get('id') == current_product.get('category_id')), None)
            if isinstance(current_product, dict):
                current_product['category_name'] = cur_cat.get('name') if cur_cat else current_product.get('category_name', '')
            else:
                # current_product pode ser um objeto não-dict em algumas resoluções; converter
                current_product = dict(current_product)
                current_product['category_name'] = cur_cat.get('name') if cur_cat else current_product.get('category_name', '')
        except Exception:
            current_product = dict(current_product)
            current_product['category_name'] = current_product.get('category_name', '')

        import unicodedata
        def normalize(s):
            if not s:
                return ''
            return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').strip().lower()

        current_category = normalize(current_product.get('category_name', ''))
        print(f"[ALT-DEBUG] Categoria normalizada do produto atual: '{current_category}' (original: '{current_product.get('category_name', '')}')")
        same_category_products = [p for p in all_products if normalize(p.get('category_name', '')) == current_category]
        print(f"[ALT-DEBUG] Produtos na mesma categoria: {len(same_category_products)}")
        for p in same_category_products:
            print(f"    - {p.get('name')} (ID: {p.get('id')})")

        alternatives = []
        current_price = current_product.get('base_price', current_product.get('price', 0))

        # Se houver mais de um produto na mesma categoria, priorizar essa lista.
        candidates = same_category_products if len(same_category_products) > 1 else []

        # Garantir que o produto atual não esteja entre os candidatos (comparar por id e por slug do nome)
        try:
            current_id_str = str(current_product.get('id') or '')
            current_name_slug = slugify(current_product.get('name') or '')
            filtered = []
            for p in candidates:
                pid = str(p.get('id') or '')
                name_slug = slugify(p.get('name') or '')
                if pid == current_id_str or (name_slug and name_slug == current_name_slug):
                    # p represents the same product; skip
                    continue
                filtered.append(p)
            candidates = filtered
        except Exception:
            pass

        # Se não houver candidatos por categoria, fallback para todos os produtos da família (excluindo o atual)
        if not candidates:
            print("[ALT-DEBUG] Nenhum produto na mesma categoria; buscando por família como fallback.")
            # Excluir explicitamente o produto atual também no fallback por família
            current_id_str = str(current_product.get('id') or '')
            current_name_slug = slugify(current_product.get('name') or '')
            candidates = [p for p in all_products if str(p.get('id')) != current_id_str and slugify(p.get('name') or '') != current_name_slug]

        # Calcular diferenças de preço e ordenar para oferecer alternativas mais próximas
        scored = []
        for product in candidates:
            try:
                pid = product.get('id')
                price = product.get('base_price', product.get('price', 0)) or 0
                diff = abs(price - (current_price or 0))
                scored.append((diff, product))
            except Exception as e:
                print(f"[ALT-DEBUG] Erro ao pontuar produto: {e}")

        scored.sort(key=lambda x: x[0])

        # Limitar a um número razoável de alternativas
        for diff, product in scored[:6]:
            alternatives.append({
                'id': product.get('id'),
                'name': product.get('name'),
                'price': product.get('base_price', product.get('price', 0)) or 0,
                'description': product.get('description', ''),
                'attributes': product.get('attributes', {})
            })
            print(f"[ALT-DEBUG] Alternativa proposta: {product.get('name')} (ID: {product.get('id')}) diff={diff}")

        print(f"[ALT-DEBUG] Total de alternativas encontradas: {len(alternatives)}")

        return jsonify({
            'success': True,
            'current_product': {
                'id': current_product['id'],
                'name': current_product['name'],
                'price': current_product.get('base_price', current_product.get('price', 0))
            },
            'alternatives': alternatives
        })
        
    except Exception as e:
        print(f"ERRO get_alternatives: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/remove_product', methods=['POST'])
def remove_product():
    """Remove um produto do orçamento completamente"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = session.get('current_budget', {})
        
        product_id = data.get('product_id')
        family_name = data.get('family')
        
        if not product_id or not family_name:
            return jsonify({'success': False, 'error': 'Parâmetros inválidos'})
        
        # Encontrar e remover o produto
        if family_name in budget.get('families', {}):
            family_products = budget['families'][family_name]
            
            if product_id in family_products:
                del family_products[product_id]
                
                # Recalcular total da família excluindo alternativos
                family_total = sum(
                    p['price'] * p['quantity'] for p in family_products.values() 
                    if p['quantity'] > 0 and p.get('item_type', 'incluido') in ['incluido', 'opcional']
                )
                
                # Recalcular totais usando a nova função
                calculate_and_update_totals(budget)
                
                session['current_budget'] = budget
                
                return jsonify({
                    'success': True,
                    'message': 'Produto removido com sucesso',
                    'new_total': budget['total_price']
                })
            else:
                return jsonify({'success': False, 'error': 'Produto não encontrado'})
        else:
            return jsonify({'success': False, 'error': 'Família não encontrada'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_product_families')
def get_product_families():
    """Retorna todas as famílias de produtos disponíveis"""
    try:
        # Serve families directly from default_data.py fallback (ignore DB entirely)
        try:
            from default_data import product_families, product_categories, products
        except Exception as ex:
            return jsonify({'success': False, 'error': f'Fallback data not available: {ex}'}), 500

        families = []
        for fam in product_families:
            fam_copy = dict(fam)
            fam_id = fam_copy.get('id')
            cat_ids = [c.get('id') for c in product_categories if c.get('family_id') == fam_id]
            fam_copy['product_count'] = sum(1 for p in products if p.get('category_id') in cat_ids and p.get('is_active', 1))
            families.append(fam_copy)

        # Add deterministic slug for client-side use
        try:
            import unicodedata, re
            def _make_slug(name: str) -> str:
                if not name:
                    return ''
                s = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII').strip().lower()
                s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
                return s
            for fam in families:
                fam['name_slug'] = _make_slug(fam.get('name') or '')
        except Exception:
            pass

        return jsonify({'success': True, 'families': families})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_family_products/<family_name>')
def get_family_products(family_name):
    """Retorna todos os produtos de uma família específica"""
    try:
        # Use fallback default_data.py as the single source of truth for modal
        try:
            from default_data import product_families, product_categories, products, product_attributes, attribute_types
        except Exception as ex:
            return jsonify({'success': False, 'error': f'Fallback data not available: {ex}'}), 500

        import unicodedata, re
        def _normalize(s: str) -> str:
            if not s:
                return ''
            s2 = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').strip().lower()
            s2 = re.sub(r'[^a-z0-9]+', '_', s2).strip('_')
            return s2

        normalized = _normalize(family_name)

        fam = next((f for f in product_families if f.get('name') == family_name or _normalize(f.get('name', '')) == normalized), None)
        if not fam:
            return jsonify({'success': True, 'products': []})

        fam_id = fam.get('id')
        cats = [c for c in product_categories if c.get('family_id') == fam_id]
        cat_ids = [c.get('id') for c in cats]

        result = []
        for prod in products:
            if prod.get('category_id') in cat_ids and prod.get('is_active', 1):
                cat = next((c for c in cats if c.get('id') == prod.get('category_id')), None)
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat.get('name') if cat else None
                prod_copy['family_name'] = fam.get('name')
                prod_copy['attributes'] = {}
                for pa in product_attributes:
                    if pa.get('product_id') == prod.get('id'):
                        attr_type = next((a for a in attribute_types if a.get('id') == pa.get('attribute_type_id')), None)
                        if not attr_type:
                            continue
                        name = attr_type.get('name')
                        data_type = attr_type.get('data_type')
                        unit = attr_type.get('unit')
                        if data_type == 'numeric':
                            prod_copy['attributes'][name] = {'value': pa.get('value_numeric'), 'unit': unit}
                        elif data_type == 'boolean':
                            prod_copy['attributes'][name] = pa.get('value_boolean')
                        else:
                            prod_copy['attributes'][name] = pa.get('value_text')
                result.append(prod_copy)

        return jsonify({'success': True, 'products': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/include_optional_product', methods=['POST'])
def include_optional_product():
    """Transforma um produto opcional em incluído no orçamento"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = session.get('current_budget', {})
        
        product_id = data.get('product_id')
        family = data.get('family')
        quantity = int(data.get('quantity', 1))
        
        print(f"DEBUG: Incluindo produto opcional {product_id} da família {family} com quantidade {quantity}")
        
        # Verificar se o produto existe no orçamento
        families_data = budget.get('selected_products', budget.get('families', {}))
        
        if family in families_data and product_id in families_data[family]:
            # Transformar o produto opcional em incluído
            families_data[family][product_id]['item_type'] = 'incluido'
            families_data[family][product_id]['quantity'] = quantity
            
            # Recalcular totais
            calculate_and_update_totals(budget)
            
            session['current_budget'] = budget
            
            return jsonify({
                'success': True,
                'message': 'Produto incluído no orçamento com sucesso',
                'new_total': budget['total_price']
            })
        else:
            return jsonify({'success': False, 'error': 'Produto não encontrado'})
            
    except Exception as e:
        print(f"ERROR: Erro ao incluir produto opcional: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/add_product', methods=['POST'])
def add_product():
    """Adiciona um novo produto ao orçamento"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        budget = get_current_budget()
        
        print(f"\n=== DEBUG ADD_PRODUCT ===")
        print(f"Data recebida: {data}")
        print(f"Budget atual existe: {bool(budget)}")
        
        product_id = data.get('product_id')
        item_type = data.get('item_type', 'incluido')  # incluido, opcional, alternativo
        alternative_to = data.get('alternative_to', None)  # Para produtos alternativos
        
        print(f"Product ID: {product_id}")
        print(f"Item Type: {item_type}")
        print(f"Alternative To: {alternative_to}")
        
        if not product_id:
            return jsonify({'success': False, 'error': 'ID do produto é obrigatório'})
        
        # Buscar informações do produto
        product = db_manager.get_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Produto não encontrado'})
        
        print(f"Produto encontrado: {product.get('name', 'Sem nome')}")
        print(f"Família do produto: {product.get('family_name', 'Sem família')}")
        
        # Determinar a família do produto (normalizar nomes para evitar fallback indevido)
        family_name = product.get('family_name', '') or ''
        print(f"DEBUG add_product - family_name do produto: '{family_name}'")

        import unicodedata, re
        def _normalize(s):
            if not s:
                return ''
            return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').strip().lower()

        normalized_family = _normalize(family_name)

        # Mapeamentos com chaves normalizadas para cobrir variações/acentos
        family_mapping_raw = {
            'filtração': 'filtracao',
            'aquecimento': 'aquecimento',
            'iluminação': 'iluminacao',
            'automação': 'automacao',
            'limpeza': 'limpeza',
            'acessórios': 'acessorios',
            'recirculação e iluminação': 'recirculacao_iluminacao'
        }
        family_mapping = { _normalize(k): v for k, v in family_mapping_raw.items() }

        # Variações adicionais normalizadas
        family_variations_raw = {
            'filtracao': 'filtracao',
            'filtração': 'filtracao',
            'filtraçao': 'filtracao',
            'filtracacão': 'filtracao',
            'aquecimento': 'aquecimento',
            'iluminacao': 'iluminacao',
            'iluminação': 'iluminacao',
            'automacao': 'automacao',
            'automação': 'automacao',
            'limpeza': 'limpeza',
            'acessorios': 'acessorios',
            'acessórios': 'acessorios',
            'recirculação e iluminação - encastráveis tanque piscina': 'recirculacao_iluminacao',
            'recirculacao e iluminacao - encastráveis tanque piscina': 'recirculacao_iluminacao',
            'recirculação e iluminação': 'recirculacao_iluminacao',
            'recirculacao e iluminacao': 'recirculacao_iluminacao'
        }
        family_variations = { _normalize(k): v for k, v in family_variations_raw.items() }

        # Tentar mapeamento direto -> variações -> fallback
        mapped_family = family_mapping.get(normalized_family) or family_variations.get(normalized_family)
        if not mapped_family:
            # Se ainda não mapeado, usar a versão slug do nome normalizado como chave
            if normalized_family:
                mapped_family = re.sub(r'[^a-z0-9]+', '_', normalized_family).strip('_')
                print(f"DEBUG add_product - fallback slug gerado para família: '{mapped_family}'")
            else:
                mapped_family = 'acessorios'

        print(f"DEBUG add_product - família mapeada: '{mapped_family}' (original: '{family_name}')")
        
        # Inicializar família se não existir
        if 'families' not in budget:
            budget['families'] = {}
        if mapped_family not in budget['families']:
            budget['families'][mapped_family] = {}
        if 'family_totals' not in budget:
            budget['family_totals'] = {}
        if mapped_family not in budget['family_totals']:
            budget['family_totals'][mapped_family] = 0.0
        
        # Criar chave única para o produto
        category_prefixes = {
            'Filtros de Areia': 'filter',
            'Filtros de Cartucho': 'filter',
            'Bombas': 'pump',
            'Válvulas': 'valve',
            'Quadros Elétricos': 'panel',
            'Refletores LED': 'led',
            'Aquecedores': 'heater'
        }
        
        category = product.get('category_name', '')
        prefix = category_prefixes.get(category, 'product')
        product_key = f"{prefix}_{product_id}"
        
        # Se for alternativo, adicionar referência ao produto relacionado
        alternative_to_product = None
        alternative_to_key = None
        if item_type == 'alternativo' and alternative_to:
            print(f"Processando produto alternativo...")
            print(f"Procurando produto principal com ID/key: {alternative_to}")
            
            # Procurar o produto principal em todas as famílias.
            # Accept both full keys (e.g. 'filter_123') or raw numeric IDs ('123').
            alt_str = str(alternative_to)
            for fam_name, fam_products in budget.get('families', {}).items():
                print(f"  Verificando família {fam_name} com {len(fam_products)} produtos")
                
                # 1) Match by exact key
                if alt_str in fam_products:
                    alternative_to_key = alt_str
                    alternative_to_product = fam_products[alt_str]
                    print(f"  ✓ Encontrado por chave exata: {alt_str}")
                    break

                # 2) Match by raw id inside product entries
                for existing_key, existing_prod in fam_products.items():
                    try:
                        existing_id = str(existing_prod.get('id', ''))
                        existing_product_id = str(existing_prod.get('product_id', ''))
                    except Exception:
                        existing_id = ''
                        existing_product_id = ''
                    
                    if (existing_id and existing_id == alt_str) or (existing_product_id and existing_product_id == alt_str):
                        alternative_to_key = existing_key
                        alternative_to_product = existing_prod
                        print(f"  ✓ Encontrado por ID interno: {existing_key} (ID: {existing_id}, Product ID: {existing_product_id})")
                        break
                if alternative_to_product:
                    break
            
            if not alternative_to_product:
                print(f"  ❌ Produto principal não encontrado!")
                print(f"  Produtos disponíveis no budget:")
                for fam_name, fam_products in budget.get('families', {}).items():
                    for prod_key, prod_data in fam_products.items():
                        print(f"    {fam_name}.{prod_key}: ID={prod_data.get('id', 'N/A')}, Name={prod_data.get('name', 'N/A')}")
            else:
                print(f"  ✓ Produto principal encontrado: {alternative_to_product.get('name', 'Sem nome')}")
        
        # Definir quantidade baseada no tipo
        quantity = 1 if item_type in ['incluido', 'alternativo'] else 0
        print(f"Quantidade definida: {quantity}")
        
        # Adicionar o novo produto
        product_data = {
            'id': product['id'],
            'name': product['name'],
            'price': product['base_price'],
            'quantity': quantity,
            'item_type': item_type,
            'unit': product.get('unit', 'un'),
            'reasoning': f'Produto adicionado manualmente pelo comercial'
        }
        
        print(f"Dados do produto criado: {product_data}")
        
        # Se for alternativo, armazenar a chave correta (product key) da referência
        if item_type == 'alternativo' and alternative_to:
            # Preferir a chave completa encontrada; se não, tentar usar o valor passado
            if alternative_to_key:
                product_data['alternative_to'] = alternative_to_key
                print(f"Definindo alternative_to como chave: {alternative_to_key}")
            else:
                # armazenar como string — pode ainda ser resolvido em fluxos posteriores
                product_data['alternative_to'] = str(alternative_to)
                print(f"Definindo alternative_to como string: {alternative_to}")

            if alternative_to_product:
                product_data['alternative_to_name'] = alternative_to_product.get('name', 'Produto Principal')
                print(f"Nome do produto principal: {product_data['alternative_to_name']}")
        
        budget['families'][mapped_family][product_key] = product_data
        print(f"Produto adicionado à família {mapped_family} com chave {product_key}")
        
        # Recalcular totais excluindo alternativos
        family_total = sum(
            p['price'] * p['quantity'] for p in budget['families'][mapped_family].values()
            if p['quantity'] > 0 and p.get('item_type', 'incluido') in ['incluido', 'opcional']
        )
        
        print(f"Total da família {mapped_family} (antes recalcular): {family_total}")
        
        # Recalcular totais usando a nova função
        calculate_and_update_totals(budget)
        
        print(f"Total do orçamento após recalcular: {budget.get('total_price', 0)}")
        
        save_current_budget(budget)
        print(f"Budget salvo (cache inteligente)")
        print(f"=== FIM DEBUG ADD_PRODUCT ===\n")
        
        return jsonify({
            'success': True,
            'message': f'Produto {product["name"]} adicionado com sucesso',
            'new_total': budget['total_price']
        })
        
    except Exception as e:
        print(f"ERRO add_product: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/restore_budget_state', methods=['POST'])
def restore_budget_state():
    """Restaura o estado do orçamento salvo anteriormente"""
    try:
        data = request.get_json()
        saved_state = data.get('budgetState')
        
        if not saved_state:
            return jsonify({'success': False, 'error': 'Nenhum estado salvo encontrado'})
        
        # Restaurar dados na sessão
        if 'budgetData' in saved_state:
            budget_data = saved_state['budgetData']
            
            # Restaurar informações básicas
            if 'client_info' in budget_data:
                session['client_info'] = budget_data['client_info']
            
            if 'pool_info' in budget_data:
                session['pool_info'] = budget_data['pool_info']
            
            # Restaurar orçamento completo
            if 'products' in budget_data:
                # Reconstruir estrutura do orçamento
                restored_budget = {
                    'client_data': budget_data.get('client_info', {}),  # Mapear client_info para client_data
                    'pool_info': budget_data.get('pool_info', {}),
                    'family_totals': budget_data.get('family_totals', {}),
                    'total_price': budget_data.get('total_price', 0),
                    'families': {}  # Criar estrutura families
                }
                
                # Organizar produtos por família
                for product_id, product_data in budget_data['products'].items():
                    family = product_data.get('family', 'acessorios')
                    if family not in restored_budget['families']:
                        restored_budget['families'][family] = []
                    restored_budget['families'][family].append(product_data)
                
                # Debug - Log estrutura do orçamento restaurado
                print(f"DEBUG: Orçamento restaurado com {len(budget_data['products'])} produtos")
                print(f"DEBUG: Famílias: {list(restored_budget['families'].keys())}")
                print(f"DEBUG: Total: {restored_budget['total_price']}")
                
                session['current_budget'] = restored_budget
        
        return jsonify({
            'success': True,
            'message': 'Estado do orçamento restaurado com sucesso',
            'redirect_url': '/budget'
        })
        
    except Exception as e:
        print(f"ERRO restore_budget_state: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_current_client_data', methods=['GET'])
def get_current_client_data():
    """Retorna os dados atuais do cliente"""
    try:
        budget = session.get('current_budget', {})
        client_data = budget.get('client_data', {})
        
        return jsonify({
            'success': True,
            'client_data': {
                'clientName': client_data.get('clientName', ''),
                'proposalNumber': client_data.get('proposalNumber', ''),
                'date': client_data.get('date', ''),
                'commercialName': client_data.get('commercialName', ''),
                'localidade': client_data.get('localidade', ''),
                'localidade_outro': client_data.get('localidade_outro', ''),
                'observations': client_data.get('observations', '')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/update_client_data', methods=['POST'])
def update_client_data():
    """Atualiza os dados do cliente na sessão"""
    try:
        # Verificar se existe um orçamento na sessão
        if 'current_budget' not in session:
            return jsonify({
                'success': False,
                'error': 'Nenhum orçamento ativo encontrado'
            }), 400
        
        data = request.form.to_dict()
        
        # Atualizar dados do cliente na sessão
        session['current_budget']['client_data'] = {
            'clientName': data.get('clientName', ''),
            'proposalNumber': data.get('proposalNumber', ''),
            'date': data.get('date', ''),
            'commercialName': data.get('commercialName', ''),
            'localidade': data.get('localidade', ''),
            'localidade_outro': data.get('localidade_outro', ''),
            'observations': data.get('observations', '')
        }
        
        # Marcar sessão como modificada
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Dados do cliente atualizados com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
