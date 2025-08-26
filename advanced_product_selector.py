# Seletor de Produtos Avançado - Integrado com Base de Dados
# Substitui o product_selector.py anterior com funcionalidade completa

from database_manager import DatabaseManager
from calculator import PoolCalculator
from typing import Dict, List, Any
import json
try:
    from flask import session
except ImportError:
    session = None  # Para casos onde Flask não está disponível

class AdvancedProductSelector:
    """Seletor avançado de produtos integrado com base de dados"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.calculator = PoolCalculator()
    
    def generate_budget(self, answers: Dict, metrics: Dict, dimensions: Dict) -> Dict:
        """Gera orçamento completo usando a base de dados"""
        # Calcular multiplicador final (novo sistema)
        final_multiplier = self.calculator.calculate_final_multiplier(answers, dimensions)
        # Obter breakdown detalhado dos multiplicadores
        multiplier_breakdown = self.calculator.get_multiplier_breakdown(answers, dimensions)
        # Obter dados do cliente da sessão (se disponível)
        client_data = {}
        if session:
            client_data = session.get('client_data', {})
        budget = {
            'pool_info': {
                'dimensions': dimensions,
                'metrics': metrics,
                'answers': answers,
                'multiplier': final_multiplier,
                'multiplier_breakdown': multiplier_breakdown
            },
            'client_data': client_data,  # Adicionar dados do cliente
            'families': {},
            'family_totals': {},
            'total_price': 0
        }
        # Condições para seleção de produtos
        conditions = {
            'location': answers.get('localizacao', 'exterior'),
            'domotics': str(answers.get('domotica', False)).lower(),
            'pool_type': answers.get('tipo_piscina', 'skimmer'),
            'coating_type': answers.get('revestimento', 'tela'),
            'power_type': answers.get('luz', 'monofasica'),
            'casa_maquinas_abaixo': answers.get('casa_maquinas_abaixo', 'nao'),
            'tipo_luzes': answers.get('tipo_luzes', 'branco_frio'),
            'tratamento_agua': answers.get('tratamento_agua', 'nao')
        }
        # Selecionar produtos por família
        filtracao = self._select_filtration_products(conditions, metrics)
        recirculacao = self._select_recirculation_lighting_products(conditions, dimensions)

        # --- Lógica para Sal Granulado Refinado ---
        import math
        tratamento_agua = {}
        volume_m3 = dimensions.get('volume', 0) or metrics.get('volume', 0) or 0
        m3_h = metrics.get('m3_h', 0)
        tratamento_tipo = conditions.get('tratamento_agua', 'nao')
        
        # Sempre adicionar sal se volume > 0
        if volume_m3 > 0:
            sal_qty = math.ceil((volume_m3 * 1000 * 0.006) / 25)
            sal_produtos = self.db.get_products_by_family('Tratamento de Água')
            sal_produto = next((p for p in sal_produtos if p['name'].lower().strip() == 'sal granulado refinado'), None)
            if sal_produto:
                tratamento_agua['sal_granulado_refinado'] = {
                    'name': sal_produto['name'],
                    'price': sal_produto['base_price'],
                    'quantity': sal_qty,
                    'unit': sal_produto['unit'],
                    'item_type': 'incluido',
                    'reasoning': f"Quantidade calculada para {volume_m3} m³ de piscina",
                    'can_change_type': False
                }

        # Lógica baseada no tipo de tratamento escolhido
        if tratamento_tipo == 'cloro_automatico':
            # Adicionar Doseador Automático RX
            doseador_produtos = self.db.get_products_by_family('Tratamento de Água')
            doseador = next((p for p in doseador_produtos if 'doseador automático rx' in p['name'].lower()), None)
            if doseador:
                tratamento_agua['doseador_automatico'] = {
                    'name': doseador['name'],
                    'price': doseador['base_price'],
                    'quantity': 1,
                    'unit': doseador['unit'],
                    'item_type': 'incluido',
                    'reasoning': 'Doseador automático selecionado',
                    'can_change_type': False
                }
        
        elif tratamento_tipo == 'clorador_salino':
            # Adicionar Inverclear baseado no volume + Proteção Anódica
            tratamento_produtos = self.db.get_products_by_family('Tratamento de Água')
            inverclear_produtos = [p for p in tratamento_produtos if 'inverclear' in p['name'].lower() and 'm3' in p['name'].lower()]
            
            # Selecionar Inverclear adequado ao volume
            melhor_inverclear = None
            for produto in inverclear_produtos:
                # Extrair capacidade do nome (ex: "40m3")
                import re
                match = re.search(r'(\d+)m3', produto['name'])
                if match:
                    capacidade = int(match.group(1))
                    if capacidade >= volume_m3:
                        if melhor_inverclear is None or capacidade < int(re.search(r'(\d+)m3', melhor_inverclear['name']).group(1)):
                            melhor_inverclear = produto
            
            if melhor_inverclear:
                tratamento_agua['inverclear'] = {
                    'name': melhor_inverclear['name'],
                    'price': melhor_inverclear['base_price'],
                    'quantity': 1,
                    'unit': melhor_inverclear['unit'],
                    'item_type': 'incluido',
                    'reasoning': f'Clorador salino selecionado para {volume_m3} m³',
                    'can_change_type': False
                }
            
            # Adicionar Proteção Anódica
            protecao = next((p for p in tratamento_produtos if 'proteção anódica' in p['name'].lower()), None)
            if protecao:
                tratamento_agua['protecao_anodica'] = {
                    'name': protecao['name'],
                    'price': protecao['base_price'],
                    'quantity': 1,
                    'unit': protecao['unit'],
                    'item_type': 'incluido',
                    'reasoning': 'Proteção anódica incluída com clorador salino',
                    'can_change_type': False
                }
        
        elif tratamento_tipo == 'clorador_salino_ph':
            # Adicionar Mr. Pure baseado no volume + Proteção Anódica
            tratamento_produtos = self.db.get_products_by_family('Tratamento de Água')
            mr_pure_produtos = [p for p in tratamento_produtos if 'mr. pure' in p['name'].lower() and 'm3' in p['name'].lower()]
            
            # Selecionar Mr. Pure adequado ao volume
            melhor_mr_pure = None
            for produto in mr_pure_produtos:
                import re
                match = re.search(r'(\d+)m3', produto['name'])
                if match:
                    capacidade = int(match.group(1))
                    if capacidade >= volume_m3:
                        if melhor_mr_pure is None or capacidade < int(re.search(r'(\d+)m3', melhor_mr_pure['name']).group(1)):
                            melhor_mr_pure = produto
            
            if melhor_mr_pure:
                tratamento_agua['mr_pure'] = {
                    'name': melhor_mr_pure['name'],
                    'price': melhor_mr_pure['base_price'],
                    'quantity': 1,
                    'unit': melhor_mr_pure['unit'],
                    'item_type': 'incluido',
                    'reasoning': f'Clorador salino + PH selecionado para {volume_m3} m³',
                    'can_change_type': False
                }
            
            # Adicionar Proteção Anódica
            protecao = next((p for p in tratamento_produtos if 'proteção anódica' in p['name'].lower()), None)
            if protecao:
                tratamento_agua['protecao_anodica'] = {
                    'name': protecao['name'],
                    'price': protecao['base_price'],
                    'quantity': 1,
                    'unit': protecao['unit'],
                    'item_type': 'incluido',
                    'reasoning': 'Proteção anódica incluída com clorador salino + PH',
                    'can_change_type': False
                }
        
        elif tratamento_tipo == 'clorador_salino_ph_uv':
            # Adicionar Mr. Pure + UV-C Titan baseado no volume e m3/h + Proteção Anódica
            tratamento_produtos = self.db.get_products_by_family('Tratamento de Água')
            
            # Selecionar Mr. Pure
            mr_pure_produtos = [p for p in tratamento_produtos if 'mr. pure' in p['name'].lower() and 'm3' in p['name'].lower()]
            melhor_mr_pure = None
            for produto in mr_pure_produtos:
                import re
                match = re.search(r'(\d+)m3', produto['name'])
                if match:
                    capacidade = int(match.group(1))
                    if capacidade >= volume_m3:
                        if melhor_mr_pure is None or capacidade < int(re.search(r'(\d+)m3', melhor_mr_pure['name']).group(1)):
                            melhor_mr_pure = produto
            
            if melhor_mr_pure:
                tratamento_agua['mr_pure'] = {
                    'name': melhor_mr_pure['name'],
                    'price': melhor_mr_pure['base_price'],
                    'quantity': 1,
                    'unit': melhor_mr_pure['unit'],
                    'item_type': 'incluido',
                    'reasoning': f'Clorador salino + PH selecionado para {volume_m3} m³',
                    'can_change_type': False
                }
            
            # Selecionar UV-C Titan baseado em m3/h
            uv_produtos = [p for p in tratamento_produtos if 'uv-c titan' in p['name'].lower() and 'm3/h' in p['name'].lower()]
            melhor_uv = None
            for produto in uv_produtos:
                import re
                match = re.search(r'(\d+)m3/h', produto['name'])
                if match:
                    capacidade = int(match.group(1))
                    if capacidade >= m3_h:
                        if melhor_uv is None or capacidade < int(re.search(r'(\d+)m3/h', melhor_uv['name']).group(1)):
                            melhor_uv = produto
            
            if melhor_uv:
                tratamento_agua['uv_titan'] = {
                    'name': melhor_uv['name'],
                    'price': melhor_uv['base_price'],
                    'quantity': 1,
                    'unit': melhor_uv['unit'],
                    'item_type': 'incluido',
                    'reasoning': f'Sistema UV selecionado para {m3_h} m³/h',
                    'can_change_type': False
                }
            
            # Adicionar Proteção Anódica
            protecao = next((p for p in tratamento_produtos if 'proteção anódica' in p['name'].lower()), None)
            if protecao:
                tratamento_agua['protecao_anodica'] = {
                    'name': protecao['name'],
                    'price': protecao['base_price'],
                    'quantity': 1,
                    'unit': protecao['unit'],
                    'item_type': 'incluido',
                    'reasoning': 'Proteção anódica incluída com clorador salino + PH + UV',
                    'can_change_type': False
                }

        # --- Lógica para família Revestimento ---
        revestimento = {}
        revestimento_tipo = conditions.get('coating_type', 'tela')
        cobertura = answers.get('cobertura', 'nao')
        tipo_cobertura_laminas = answers.get('tipo_cobertura_laminas', '')
        tipo_construcao = answers.get('tipo_construcao', 'nova')
        forma_piscina = answers.get('forma_piscina', 'standard')  # Adapte se o nome do campo for diferente

        if revestimento_tipo == 'tela':
            comprimento = dimensions.get('comprimento', 0)
            largura = dimensions.get('largura', 0)
            bordadura = metrics.get('ml_bordadura', 0)
            revestimento_produtos = self.db.get_products_by_family('Revestimento')
            quantidades = answers.get('quantidades', {})

            # Lógica só para forma standard
            if forma_piscina == 'standard':
                # Fórmulas de rolos
                if cobertura == 'laminas' and tipo_cobertura_laminas in ['submersa_praia', 'fora_praia']:
                    # Fórmula 1
                    x = (comprimento + largura) * 2 + largura + largura + (comprimento / 1.6) * largura
                else:
                    # Fórmula 2
                    x = (comprimento + largura) * 2 + (comprimento / 1.6) * 2
                rolos_qty = math.ceil(x / 25) if x > 0 else 0

                # Produto padrão: Revestimento Tela Armada 3D Unicolor CGT Vg 1
                tela_produto = next((p for p in revestimento_produtos if 'tela armada 3d unicolor' in p['name'].lower() and 'cgt' in p['name'].lower()), None)
                # Alternativas
                tela_3d = next((p for p in revestimento_produtos if 'tela armada 3d' in p['name'].lower() and 'cgt' in p['name'].lower() and 'unicolor' not in p['name'].lower()), None)
                tela_lisa = next((p for p in revestimento_produtos if 'tela armada lisa' in p['name'].lower() and 'cgt' in p['name'].lower()), None)
                tela_alternatives = []
                if tela_3d:
                    tela_alternatives.append({'id': tela_3d['id'], 'name': tela_3d['name'], 'price': tela_3d['base_price']})
                if tela_lisa:
                    tela_alternatives.append({'id': tela_lisa['id'], 'name': tela_lisa['name'], 'price': tela_lisa['base_price']})
                if tela_produto and rolos_qty > 0:
                    key = f"tela_armada"
                    q_override = quantidades.get(key)
                    revestimento[key] = {
                        'name': tela_produto['name'],
                        'price': tela_produto['base_price'],
                        'quantity': int(q_override) if q_override is not None else rolos_qty,
                        'unit': tela_produto['unit'],
                        'item_type': 'incluido',
                        'reasoning': f'Quantidade calculada: {rolos_qty} rolos de 25m cada',
                        'can_change_type': True,
                        'alternatives': tela_alternatives,
                        'product_id': tela_produto['id']
                    }

                # Perfis
                perfil_horizontal = next((p for p in revestimento_produtos if 'perfil horizontal' in p['name'].lower()), None)
                perfil_vertical = next((p for p in revestimento_produtos if 'perfil vertical' in p['name'].lower()), None)
                chapa_colaminada = next((p for p in revestimento_produtos if 'chapa colaminada' in p['name'].lower()), None)
                perfil_produto = perfil_horizontal if tipo_construcao == 'nova' else perfil_vertical
                if bordadura > 0 and perfil_produto:
                    perfis_qty = math.ceil(bordadura / 2)
                    perfil_alternatives = []
                    if chapa_colaminada:
                        perfil_alternatives.append({'id': chapa_colaminada['id'], 'name': chapa_colaminada['name'], 'price': chapa_colaminada['base_price']})
                    key_perfil = "perfil"
                    q_override_perfil = quantidades.get(key_perfil)
                    revestimento[key_perfil] = {
                        'name': perfil_produto['name'],
                        'price': perfil_produto['base_price'],
                        'quantity': int(q_override_perfil) if q_override_perfil is not None else perfis_qty,
                        'unit': perfil_produto['unit'],
                        'item_type': 'incluido',
                        'reasoning': f'Perfil {"horizontal" if tipo_construcao == "nova" else "vertical"}: {perfis_qty} un (2ml cada)',
                        'can_change_type': True,
                        'alternatives': perfil_alternatives,
                        'product_id': perfil_produto['id']
                    }
                    # Chapa Colaminada como alternativa funcional (item_type alternativo)
                    if chapa_colaminada:
                        key_chapa = "chapa_colaminada"
                        q_override_chapa = quantidades.get(key_chapa)
                        revestimento[key_chapa] = {
                            'name': chapa_colaminada['name'],
                            'price': chapa_colaminada['base_price'],
                            'quantity': int(q_override_chapa) if q_override_chapa is not None else perfis_qty,
                            'unit': chapa_colaminada['unit'],
                            'item_type': 'alternativo',
                            'reasoning': f'Alternativa à {"horizontal" if tipo_construcao == "nova" else "vertical"}: {perfis_qty} un (2ml cada)',
                            'alternative_to': 'perfil',
                            'can_change_type': False,
                            'product_id': chapa_colaminada['id']
                        }
            else:
                # Forma especial: 1 rolo padrão
                tela_produto = next((p for p in revestimento_produtos if 'tela armada 3d unicolor' in p['name'].lower() and 'cgt' in p['name'].lower()), None)
                if tela_produto:
                    revestimento['tela_armada'] = {
                        'name': tela_produto['name'],
                        'price': tela_produto['base_price'],
                        'quantity': 1,
                        'unit': tela_produto['unit'],
                        'item_type': 'incluido',
                        'reasoning': 'Forma especial: 1 rolo padrão',
                        'can_change_type': True,
                        'alternatives': [],
                        'product_id': tela_produto['id']
                    }
        # Nenhuma lógica para cerâmica. Só executa lógica de revestimento se for tela.

        # ORDEM FILTRACAO
        filtracao_order = ['filter', 'valve', 'pump', 'vidro', 'quadro']
        def filtracao_sort_key(k):
            for idx, prefix in enumerate(filtracao_order):
                if k.startswith(prefix):
                    return idx
            return len(filtracao_order)
        filtracao_sorted = dict(sorted(filtracao.items(), key=lambda x: filtracao_sort_key(x[0])))
        # ORDEM RECIRCULACAO
        recirc_order = ['skimmer', 'boca_impulsao', 'tomada_aspiracao', 'passamuros', 'regulador_nivel', 'regulador_pack', 'ralo_fundo', 'iluminacao']
        def recirc_sort_key(k):
            for idx, prefix in enumerate(recirc_order):
                if k.startswith(prefix):
                    return idx
            return len(recirc_order)
        recirculacao_sorted = dict(sorted(recirculacao.items(), key=lambda x: recirc_sort_key(x[0])))
        # --- CORREÇÃO GERAL: Manter quantidade e posição ao trocar alternativo/incluído em qualquer família ---
        def swap_item_preserve_quantity_and_position(family_dict, selected_key=None, previous_key=None):
            # Se não houver troca válida, retorna igual
            if not (selected_key and previous_key and previous_key in family_dict):
                return family_dict
            prev_qty = family_dict[previous_key].get('quantity', 1)
            # Construir lista de pares para manipular por índice
            items = list(family_dict.items())
            # Encontrar índices
            prev_index = next((i for i, (k, v) in enumerate(items) if k == previous_key), None)
            sel_index = next((i for i, (k, v) in enumerate(items) if k == selected_key), None)

            # Preparar alt_item (se já existir, copiar e atualizar quantidade)
            if sel_index is not None:
                alt_item = dict(items[sel_index][1])
                alt_item['quantity'] = prev_qty
            else:
                # Tentar construir a partir de alternativas do previous
                alt_model = None
                prev_item = items[prev_index][1]
                if 'alternatives' in prev_item:
                    for alt in prev_item['alternatives']:
                        # tentar casar por product id ou name
                        if str(alt.get('id')) in str(selected_key) or alt.get('name') and alt.get('name').lower() in selected_key.lower():
                            alt_model = alt
                            break
                if alt_model:
                    alt_item = {
                        'name': alt_model['name'],
                        'price': alt_model['price'],
                        'quantity': prev_qty,
                        'unit': prev_item.get('unit', ''),
                        'item_type': 'alternativo',
                        'reasoning': prev_item.get('reasoning', ''),
                        'alternative_to': previous_key,
                        'can_change_type': False,
                        'product_id': alt_model['id']
                    }
                else:
                    # fallback: copiar previous e ajustar
                    alt_item = dict(prev_item)
                    alt_item['quantity'] = prev_qty
                    alt_item['item_type'] = 'alternativo'
                    alt_item['alternative_to'] = previous_key

            # Remover ocorrência existente do selected_key para evitar duplicatas
            if sel_index is not None:
                # remover o elemento da lista
                items.pop(sel_index)
                # se sel_index antes de prev_index, prev_index diminui 1
                if sel_index < prev_index:
                    prev_index -= 1

            # Substituir o elemento no índice prev_index pelo selected_key
            items[prev_index] = (selected_key, alt_item)

            # Reconstruir dict mantendo ordem
            new_dict = {k: v for k, v in items}
            return new_dict

        families_ordered = {}
        # Para cada família, aplicar swap se necessário
        for fam_name, fam_dict in [('filtracao', filtracao_sorted), ('recirculacao_iluminacao', recirculacao_sorted), ('tratamento_agua', tratamento_agua), ('revestimento', revestimento)]:
            if fam_dict:
                selected_key = None
                previous_key = None
                # Exemplo: answers['revestimento_selected'] e answers['revestimento_previous']
                if f'{fam_name}_selected' in answers and f'{fam_name}_previous' in answers:
                    selected_key = answers[f'{fam_name}_selected']
                    previous_key = answers[f'{fam_name}_previous']
                families_ordered[fam_name] = swap_item_preserve_quantity_and_position(fam_dict, selected_key, previous_key)
        budget['families'] = families_ordered
        # Calcular totais excluindo alternativos
        for family_name, family_items in budget['families'].items():
            family_total = sum(
                item['price'] * item['quantity']
                for item in family_items.values()
                if item['quantity'] > 0 and item.get('item_type', 'incluido') in ['incluido', 'opcional']
            )
            # Aplicar multiplicador
            family_total_with_multiplier = family_total * final_multiplier
            budget['family_totals'][family_name] = round(family_total_with_multiplier, 2)
        # Total geral
        budget['total_price'] = sum(budget['family_totals'].values())
        return budget
    
    def _select_filtration_products(self, conditions: Dict, metrics: Dict) -> Dict:
        """Seleciona produtos de filtração baseado nas condições"""
        products = {}
        m3_h = metrics.get('m3_h', 0)
        power_type = conditions.get('power_type', 'monofasica')
        
        # BOMBAS DE FILTRAÇÃO - LÓGICA IMPLEMENTADA COM VELOCIDADE VARIÁVEL
        suitable_pumps = self._get_suitable_pumps(m3_h, power_type)
        
        # Ordenar bombas: incluídas primeiro, depois alternativas
        suitable_pumps.sort(key=lambda x: (x['item_type'] != 'incluido', x.get('capacity_value', 0)))
        
        main_pump_id = None
        for i, pump in enumerate(suitable_pumps):
            item_type = pump.get('item_type', 'incluido')
            quantity = 0 if item_type == 'opcional' else 1
            
            # Sufixo no nome baseado no tipo
            name_suffix = ''
            if item_type == 'opcional':
                name_suffix = ' (OPCIONAL)'
            elif item_type == 'alternativo':
                name_suffix = ' (ALTERNATIVO)'
            
            # Usar numeração sequencial para manter ordem
            pump_key = f"pump_{i+1:02d}_{pump['id']}"
            
            # Se é a primeira bomba, é a principal
            if i == 0:
                main_pump_id = pump_key
            
            pump_data = {
                'name': pump['name'] + name_suffix,
                'price': pump['base_price'],
                'quantity': quantity,
                'unit': pump['unit'],
                'item_type': item_type,
                'reasoning': pump.get('reasoning', f'Bomba selecionada para {m3_h} m³/h - {power_type}'),
                'can_change_type': True
            }
            
            # Se é alternativo e temos bomba principal, linkar
            if item_type == 'alternativo' and main_pump_id:
                pump_data['alternative_to'] = main_pump_id
            
            products[pump_key] = pump_data
        
        # VÁLVULAS - LÓGICA COMPLETA IMPLEMENTADA  
        valve_products = self._get_suitable_valves(conditions['domotics'])
        main_valve_key = None
        for i, valve in enumerate(valve_products):
            item_type = valve.get('item_type', 'incluido')
            quantity = 0 if item_type in ['opcional'] else 1
            name_suffix = ''
            if item_type == 'opcional':
                name_suffix = ' (OPCIONAL)'
            elif item_type == 'alternativo':
                name_suffix = ' (ALTERNATIVO)'
            valve_key = f"valve_{i+1:02d}_{valve['id']}"
            if item_type == 'incluido' and main_valve_key is None:
                main_valve_key = valve_key
            valve_data = {
                'name': valve['name'] + name_suffix,
                'price': valve['base_price'],
                'quantity': quantity,
                'unit': valve['unit'],
                'item_type': item_type,
                'reasoning': valve.get('reasoning', 'Válvula selecionada automaticamente'),
                'can_change_type': True
            }
            # Se for alternativo, garantir que alternative_to aponte para a principal
            if item_type == 'alternativo' and main_valve_key:
                valve_data['alternative_to'] = main_valve_key
            products[valve_key] = valve_data
        
    # FILTROS - IMPLEMENTADO
        location = conditions.get('location', 'exterior')
        suitable_filters = self._get_suitable_filters(location, m3_h)

        # Tabela de capacidades de areia (kg) por filtro Aster Astralpool
        sand_capacity_kg_map = {
            'D.450': 70,
            'D.500': 90,
            'D.600': 125,
            'D.750': 210,
            'D.900': 515
        }

        # IDs dos produtos de vidro (ajuste se necessário)
        vidro_fino_id = None
        vidro_grosso_id = None
        vidros = self.db.get_products_by_category(5)  # Categoria 'Vidros e Visores' (ID: 5)
        for v in vidros:
            if '0,4-1,0mm' in v['name']:
                vidro_fino_id = v['id']
            elif '1,5-3,0mm' in v['name'] or '1.5-3.0mm' in v['name']:
                vidro_grosso_id = v['id']

        if suitable_filters:
            best_filter = suitable_filters[0]
            filter_key = f"filter_01_{best_filter['id']}"
            products[filter_key] = {
                'name': best_filter['name'],
                'price': best_filter['base_price'],
                'quantity': 1,
                'unit': best_filter['unit'],
                'item_type': 'incluido',
                'reasoning': f"Filtro selecionado para piscina {location} com capacidade {m3_h} m³/h",
                'can_change_type': True  # Permitir troca de filtro
            }

            # (Removido: a adição de válvula já é feita no bloco principal)

            # --- Lógica de vidro filtrante ---
            # Detectar modelo do filtro pelo nome
            sand_capacity_kg = None
            for key, val in sand_capacity_kg_map.items():
                if key in best_filter['name']:
                    sand_capacity_kg = val
                    break

            # IDs dos produtos de areia fina e grossa (inseridos manualmente, buscar pelo nome)
            areia_fina = None
            areia_grossa = None
            areias = self.db.get_products_by_category(5)
            for a in areias:
                if '0,6-1,2mm' in a['name'] and 'Areia' in a['name']:
                    areia_fina = a
                elif 'Grossa' in a['name'] and 'Areia' in a['name']:
                    areia_grossa = a

            if sand_capacity_kg and vidro_fino_id and vidro_grosso_id and areia_fina and areia_grossa:
                # 1. Separar areia fina e grossa
                areia_fina_kg = sand_capacity_kg * 0.7
                areia_grossa_kg = sand_capacity_kg * 0.3
                # 2. Converter para vidro (multiplicar por 0.75)
                vidro_fino_kg = areia_fina_kg * 0.75
                vidro_grosso_kg = areia_grossa_kg * 0.75
                # 3. Calcular sacos de vidro (20kg)
                import math
                n_sacos_vidro_fino = math.ceil(vidro_fino_kg / 20)
                n_sacos_vidro_grosso = math.ceil(vidro_grosso_kg / 20)
                # 4. Calcular sacos de areia (25kg)
                n_sacos_areia_fina = math.ceil(areia_fina_kg / 25)
                n_sacos_areia_grossa = math.ceil(areia_grossa_kg / 25)

                # Buscar info dos produtos de vidro
                vidro_fino = next((v for v in vidros if v['id'] == vidro_fino_id), None)
                vidro_grosso = next((v for v in vidros if v['id'] == vidro_grosso_id), None)

                # Adicionar apenas um item por tipo de vidro e areia alternativa, com a quantidade total
                if vidro_fino and areia_fina:
                    vidro_key = f"vidro_fino_{vidro_fino_id}_{filter_key}"
                    areia_key = f"areia_fina_{areia_fina['id']}_{filter_key}"
                    products[vidro_key] = {
                        'name': vidro_fino['name'],
                        'price': vidro_fino['base_price'],
                        'quantity': n_sacos_vidro_fino,
                        'unit': vidro_fino['unit'],
                        'item_type': 'incluido',
                        'reasoning': f"Vidro filtrante fino: {n_sacos_vidro_fino} sacos (70% do total de vidro)",
                        'can_change_type': False
                    }
                    products[areia_key] = {
                        'name': areia_fina['name'],
                        'price': areia_fina['base_price'],
                        'quantity': n_sacos_areia_fina,
                        'unit': areia_fina['unit'],
                        'item_type': 'alternativo',
                        'reasoning': f"Alternativa ao vidro filtrante fino: {n_sacos_areia_fina} sacos (areia fina)",
                        'alternative_to': vidro_key,
                        'can_change_type': False
                    }
                if vidro_grosso and areia_grossa:
                    vidro_key = f"vidro_grosso_{vidro_grosso_id}_{filter_key}"
                    areia_key = f"areia_grossa_{areia_grossa['id']}_{filter_key}"
                    products[vidro_key] = {
                        'name': vidro_grosso['name'],
                        'price': vidro_grosso['base_price'],
                        'quantity': n_sacos_vidro_grosso,
                        'unit': vidro_grosso['unit'],
                        'item_type': 'incluido',
                        'reasoning': f"Vidro filtrante grosso: {n_sacos_vidro_grosso} sacos (30% do total de vidro)",
                        'can_change_type': False
                    }
                    products[areia_key] = {
                        'name': areia_grossa['name'],
                        'price': areia_grossa['base_price'],
                        'quantity': n_sacos_areia_grossa,
                        'unit': areia_grossa['unit'],
                        'item_type': 'alternativo',
                        'reasoning': f"Alternativa ao vidro filtrante grosso: {n_sacos_areia_grossa} sacos (areia grossa)",
                        'alternative_to': vidro_key,
                        'can_change_type': False
                    }

        # Corrigir agrupamento visual dos alternativos da válvula (garantia extra)
        # Após todos os produtos montados, garantir que toda válvula alternativa aponte para a principal
        if main_valve_key:
            for k, v in products.items():
                if v.get('item_type') == 'alternativo' and 'Válvula' in v.get('name', ''):
                    v['alternative_to'] = main_valve_key

        return products
    
    def _get_suitable_filters(self, location: str, required_m3_h: float) -> List[Dict]:
        """Encontra filtros adequados para a localização e capacidade"""
        
        # Determinar tipo de filtro baseado na localização
        filter_conditions = {'location': location}
        
        # Obter produtos que atendem às condições
        products = self.db.get_products_by_conditions(filter_conditions)
        
        # Filtrar por capacidade e ordenar
        suitable_products = []
        for product in products:
            if product['category_name'] in ['Filtros de Areia', 'Filtros de Cartucho']:
                capacity = product['attributes'].get('Capacidade', {})
                if isinstance(capacity, dict):
                    capacity_value = capacity.get('value', 0)
                else:
                    capacity_value = float(capacity) if capacity else 0
                
                if capacity_value >= required_m3_h:
                    product['capacity_value'] = capacity_value
                    suitable_products.append(product)
        
        # Ordenar por capacidade (menor primeiro)
        suitable_products.sort(key=lambda x: x.get('capacity_value', 0))
        
        return suitable_products
    
    def _get_suitable_valves(self, has_domotics: str) -> List[Dict]:
        """Seleciona válvulas baseado na automação - LÓGICA CORRETA IMPLEMENTADA"""
        # Obter todas as válvulas
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE pc.name = 'Válvulas' AND p.is_active = 1
        """)
        
        valves = []
        for row in cursor.fetchall():
            valve = dict(row)
            valve['attributes'] = self.db.get_product_attributes(valve['id'])
            valves.append(valve)
        
        conn.close()
        
        # Separar válvulas por tipo
        manual_valves = [v for v in valves if 'Manual' in v['name']]
        auto_valves = [v for v in valves if 'iWash' in v['name'] or 'Automática' in v['name']]
        
        result = []
        
        if has_domotics == 'true':
            # COM DOMÓTICA: Automática INCLUÍDA por padrão, Manual ALTERNATIVA
            for valve in auto_valves:
                valve['item_type'] = 'incluido'
                valve['reasoning'] = 'Válvula automática para integração domótica'
                result.append(valve)
            
            for valve in manual_valves:
                valve['item_type'] = 'alternativo'
                valve['reasoning'] = 'Alternativa manual'
                result.append(valve)
        else:
            # SEM DOMÓTICA: Manual INCLUÍDA por padrão, Automática ALTERNATIVA
            for valve in manual_valves:
                valve['item_type'] = 'incluido'
                valve['reasoning'] = 'Válvula manual padrão'
                result.append(valve)
            
            for valve in auto_valves:
                valve['item_type'] = 'alternativo'
                valve['reasoning'] = 'Upgrade automático alternativo'
                result.append(valve)
        
        return result
    
    def _get_suitable_pumps(self, required_m3_h: float, power_type: str) -> List[Dict]:
        """Seleciona bombas baseado na capacidade e tipo de energia - COM VELOCIDADE VARIÁVEL"""
        
        # Obter todas as bombas de filtração da categoria "Bombas" 
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE pc.name = 'Bombas' AND p.is_active = 1
            ORDER BY p.base_price
        """)
        
        pumps = []
        for row in cursor.fetchall():
            pump = dict(row)
            pump['attributes'] = self.db.get_product_attributes(pump['id'])
            pumps.append(pump)
        
        conn.close()
        
        # Separar bombas por tipo
        standard_pumps = []
        variable_speed_pumps = []
        
        for pump in pumps:
            # Obter capacidade
            capacity = pump['attributes'].get('Capacidade', 0)
            if isinstance(capacity, dict):
                capacity_value = capacity.get('value', 0)
            else:
                capacity_value = float(capacity) if capacity else 0
            
            # Obter tipo de fase
            fase = str(pump['attributes'].get('Fase', '')).lower()
            
            # Obter tipo de bomba
            tipo_bomba = pump['attributes'].get('Tipo Bomba', 'standard')
            
            # Verificar se a capacidade atende ao requisito
            if capacity_value < required_m3_h:
                continue
            
            pump['capacity_value'] = capacity_value
            
            # Separar por tipo de bomba
            if tipo_bomba == 'velocidade_variavel':
                variable_speed_pumps.append(pump)
            else:
                standard_pumps.append(pump)
        
        # Filtrar e selecionar bombas adequadas
        suitable_pumps = []
        
        # 1. BOMBA NORMAL (INCLUÍDA)
        for pump in standard_pumps:
            fase = str(pump['attributes'].get('Fase', '')).lower()
            
            # Verificar compatibilidade de fase
            is_suitable = False
            if power_type == 'monofasica' and 'monofasica' in fase:
                is_suitable = True
            elif power_type == 'trifasica' and 'trifasica' in fase:
                is_suitable = True
            
            if is_suitable:
                pump['item_type'] = 'incluido'
                pump['reasoning'] = f'Bomba padrão: {pump["capacity_value"]}m³/h ({power_type})'
                suitable_pumps.append(pump)
                break  # Apenas a primeira (menor capacidade adequada)
        
        # 2. BOMBA VELOCIDADE VARIÁVEL (ALTERNATIVA - APENAS MONOFÁSICA)
        if power_type == 'monofasica':
            for pump in variable_speed_pumps:
                fase = str(pump['attributes'].get('Fase', '')).lower()
                
                # Velocidade variável: todas são monofásicas
                if 'monofasica' in fase:
                    pump['item_type'] = 'alternativo'
                    pump['reasoning'] = f'Eficiência energética: {pump["capacity_value"]}m³/h (velocidade variável)'
                    suitable_pumps.append(pump)
                    break  # Apenas a primeira adequada
        
        # Ordenar: incluída primeiro, depois alternativa
        suitable_pumps.sort(key=lambda x: (x['item_type'] != 'incluido', x.get('capacity_value', 0)))
        
        return suitable_pumps
    
    def _get_suitable_quadros(self, has_domotics: str, m3_h: float = 0) -> List[Dict]:
        """Seleciona quadros elétricos baseado na automação"""
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE pc.name = 'Quadros Elétricos' AND p.is_active = 1
            ORDER BY p.base_price
        """)
        
        quadros = []
        for row in cursor.fetchall():
            quadro = dict(row)
            quadro['attributes'] = self.db.get_product_attributes(quadro['id'])
            quadros.append(quadro)
        
        conn.close()
        
        suitable_quadros = []
        
        if has_domotics == 'true':
            # Com domótica: priorizar quadros inteligentes
            for quadro in quadros:
                if (quadro['attributes'].get('Automacao') == 'Sim' or 
                    'IGARDEN' in quadro['name'] or 
                    'Bluetooth' in quadro['name']):
                    
                    if 'IGARDEN' in quadro['name']:
                        quadro['reasoning'] = 'Quadro inteligente iGarden para domótica avançada'
                        quadro['priority'] = 100
                    elif 'Bluetooth' in quadro['name']:
                        quadro['reasoning'] = 'Quadro H-Power com Bluetooth para domótica básica'
                        quadro['priority'] = 80
                    else:
                        quadro['reasoning'] = 'Quadro com automação'
                        quadro['priority'] = 60
                    
                    suitable_quadros.append(quadro)
        else:
            # Sem domótica: quadros básicos Astralpool
            for quadro in quadros:
                if (quadro['attributes'].get('Automacao') != 'Sim' and 
                    'Astralpool' in quadro['brand']):
                    quadro['reasoning'] = 'Quadro básico para instalação standard'
                    quadro['priority'] = 50
                    suitable_quadros.append(quadro)
        
        # Ordenar por prioridade
        suitable_quadros.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return suitable_quadros[:2]  # Máximo 2 opções
    
    def _get_suitable_vidros(self) -> List[Dict]:
        """Obtém vidros granulados disponíveis"""
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, pc.name as category_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE pc.name = 'Vidros e Visores' AND p.is_active = 1
            ORDER BY p.base_price
        """)
        
        vidros = []
        for row in cursor.fetchall():
            vidro = dict(row)
            vidro['attributes'] = self.db.get_product_attributes(vidro['id'])
            
            # Priorizar granulometria média (1.5-3.0mm) como padrão
            if '1.5-3.0mm' in vidro['name']:
                vidro['priority'] = 100
                vidro['reasoning'] = 'Granulometria recomendada para filtração'
            else:
                vidro['priority'] = 50
                vidro['reasoning'] = 'Granulometria alternativa'
            
            vidros.append(vidro)
        
        conn.close()
        
        # Ordenar por prioridade
        vidros.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return vidros[:1]  # Apenas 1 tipo como padrão

    def _select_recirculation_lighting_products(self, conditions: Dict, dimensions: Dict) -> Dict:
        """Seleciona produtos de recirculação e iluminação baseado nas condições"""
        products = {}
        
        largura = dimensions.get('largura', 0)
        pool_type = conditions.get('pool_type', 'skimmer')
        coating_type = conditions.get('coating_type', 'tela')
        
        # SKIMMERS
        if pool_type == 'skimmer':  # Mudança: era 'standard', agora é 'skimmer'
            # Quantidade baseada na largura
            if largura <= 3.5:
                qtd_skimmers = 1
            elif largura <= 5.0:
                qtd_skimmers = 2
            else:
                qtd_skimmers = 3
            
            # Tipo baseado no revestimento
            skimmer_name = "Skimmer Linha de água Branco Liner" if coating_type == 'tela' else "Skimmer Linha de água Branco Betão"
            
            # Buscar produto na base de dados
            skimmer_product = self._get_product_by_name_pattern(skimmer_name)
            if skimmer_product:
                products[f"skimmer_{skimmer_product['id']}"] = {
                    'name': skimmer_product['name'],
                    'price': skimmer_product['base_price'],
                    'quantity': qtd_skimmers,
                    'unit': skimmer_product['unit'],
                    'item_type': 'incluido',
                    'reasoning': f"Skimmers para piscina {pool_type} {largura}m de largura",
                    'can_change_type': True
                }
        
        # BOCAS DE IMPULSÃO
        # Quantidade baseada na largura
        if largura <= 3.0:
            qtd_bocas = 2
        elif largura <= 4.5:
            qtd_bocas = 3
        else:
            qtd_bocas = 4
        
        # Tipo baseado no tipo de piscina e revestimento
        if pool_type in ['skimmer', 'transbordo']:
            if coating_type == 'tela':
                boca_name = "Boca de Impulsão de parede Astralpool Liner"
            else:
                boca_name = "Boca de Impulsão de parede Astralpool Betão"
        else:  # espelho d'água
            if coating_type == 'tela':
                boca_name = "Boca de Impulsão de fundo Astralpool Liner"
            else:
                boca_name = "Boca de Impulsão de fundo Astralpool Betão"
        
        boca_product = self._get_product_by_name_pattern(boca_name)
        if boca_product:
            products[f"boca_impulsao_{boca_product['id']}"] = {
                'name': boca_product['name'],
                'price': boca_product['base_price'],
                'quantity': qtd_bocas,
                'unit': boca_product['unit'],
                'item_type': 'incluido',
                'reasoning': f"Bocas de impulsão para piscina {largura}m de largura",
                'can_change_type': True
            }
        
        # TOMADAS DE ASPIRAÇÃO
        tomada_name = "Tomada de Aspiração Astralpool Liner" if coating_type == 'tela' else "Tomada de Aspiração Astralpool Betão"
        
        tomada_product = self._get_product_by_name_pattern(tomada_name)
        if tomada_product:
            products[f"tomada_aspiracao_{tomada_product['id']}"] = {
                'name': tomada_product['name'],
                'price': tomada_product['base_price'],
                'quantity': 1,  # Sempre 1 tomada
                'unit': tomada_product['unit'],
                'item_type': 'incluido',
                'reasoning': "Tomada de aspiração padrão",
                'can_change_type': True
            }
        
        # PASSAMUROS
        if coating_type == 'tela':
            passamuro_name = "Passamuros Astralpool Liner"  # Sempre Liner conforme especificado
        else:
            passamuro_name = "Passamuros Astralpool Betão"
        
        # Quantidade baseada no tipo de boca de impulsão
        is_fundo = "fundo" in boca_name.lower()
        qtd_passamuros = 1 if is_fundo else (1 + qtd_bocas)  # 1 tomada + bocas (se parede)
        
        passamuro_product = self._get_product_by_name_pattern(passamuro_name)
        if passamuro_product:
            products[f"passamuros_{passamuro_product['id']}"] = {
                'name': passamuro_product['name'],
                'price': passamuro_product['base_price'],
                'quantity': qtd_passamuros,
                'unit': passamuro_product['unit'],
                'item_type': 'incluido',
                'reasoning': f"Passamuros para instalação ({qtd_passamuros} unidades)",
                'can_change_type': True
            }
        
        # REGULADORES DE NÍVEL (apenas para skimmer)
        if pool_type == 'skimmer':
            regulador_name = "Regulador de Nível Astralpool"
            regulador_product = self._get_product_by_name_pattern(regulador_name)
            
            if regulador_product:
                products[f"regulador_nivel_{regulador_product['id']}"] = {
                    'name': regulador_product['name'],
                    'price': regulador_product['base_price'],
                    'quantity': 1,
                    'unit': regulador_product['unit'],
                    'item_type': 'incluido',
                    'reasoning': "Regulador de nível para piscina skimmer",
                    'can_change_type': True
                }
                
                # Pack do regulador: boca impulsão + passamuro adicionais
                pack_boca_name = "Boca de Impulsão de parede Astralpool Liner" if coating_type == 'tela' else "Boca de Impulsão de parede Astralpool Betão"
                pack_passamuro_name = "Passamuros Astralpool Liner" if coating_type == 'tela' else "Passamuros Astralpool Betão"
                
                pack_boca_product = self._get_product_by_name_pattern(pack_boca_name)
                pack_passamuro_product = self._get_product_by_name_pattern(pack_passamuro_name)
                
                if pack_boca_product:
                    products[f"regulador_pack_boca_{pack_boca_product['id']}"] = {
                        'name': "    [Pack] " + pack_boca_product['name'] + " (Pack Regulador)",
                        'price': pack_boca_product['base_price'],
                        'quantity': 1,
                        'unit': pack_boca_product['unit'],
                        'item_type': 'incluido',
                        'reasoning': "Boca impulsão adicional para regulador de nível",
                        'can_change_type': False,
                        'pack_parent': f"regulador_nivel_{regulador_product['id']}",
                        'is_pack_item': True,
                        'pack_style': 'indented'
                    }
                
                if pack_passamuro_product:
                    products[f"regulador_pack_passamuro_{pack_passamuro_product['id']}"] = {
                        'name': "    [Pack] " + pack_passamuro_product['name'] + " (Pack Regulador)",
                        'price': pack_passamuro_product['base_price'],
                        'quantity': 1,
                        'unit': pack_passamuro_product['unit'],
                        'item_type': 'incluido',
                        'reasoning': "Passamuro adicional para regulador de nível",
                        'can_change_type': False,
                        'pack_parent': f"regulador_nivel_{regulador_product['id']}",
                        'is_pack_item': True,
                        'pack_style': 'indented'
                    }
        
        # ILUMINAÇÃO
        comprimento = dimensions.get('comprimento', 0)
        
        # RALOS DE FUNDO - baseados no tipo de revestimento e área da piscina
        area_piscina = dimensions.get('comprimento', 0) * dimensions.get('largura', 0)
        
        # Determinar quantidade de ralos (fixado para 1)
        qtd_ralos = 1

        # Selecionar ralo baseado no revestimento
        if coating_type == 'tela':
            ralo_name = "Ralo de fundo Kripsol Liner"
        else:  # betão
            ralo_name = "Ralo de fundo Kripsol Betão"
        
        ralo_product = self._get_product_by_name_pattern(ralo_name)
        if ralo_product:
            products[f"ralo_fundo_{ralo_product['id']}"] = {
                'name': ralo_product['name'],
                'price': ralo_product['base_price'],
                'quantity': qtd_ralos,
                'unit': ralo_product['unit'],
                'item_type': 'incluido',
                'reasoning': f"Ralo de fundo para piscina {area_piscina:.1f}m² ({coating_type})",
                'can_change_type': True
            }
        tipo_luzes = conditions.get('tipo_luzes', 'branco_frio')
        
        # 1. Determinar tamanho das luzes baseado na largura
        if largura <= 2.5:
            tamanho_mm = 50
            tipo_base = "Projector Led Luz Branca"
        elif largura <= 4.0:
            tamanho_mm = 100
            tipo_base = "Projector Led Luz Branco Adaptável"
        else:  # largura > 4.0
            tamanho_mm = 170
            tipo_base = "Projector Led Luz RGB"
        
        # 2. Ajustar tipo baseado na preferência do usuário
        if tipo_luzes == 'branco_frio':
            luz_name = f"Projector Led Luz Branca de {tamanho_mm}mm"
        elif tipo_luzes == 'branco_adaptavel':
            luz_name = f"Projector Led Luz Branco Adaptável de {tamanho_mm}mm"
        else:  # rgb
            luz_name = f"Projector Led Luz RGB de {tamanho_mm}mm"
        
        # 3. Determinar quantidade baseada no comprimento
        if comprimento <= 7.0:
            qtd_luzes = 2
        elif comprimento <= 9.5:
            qtd_luzes = 3
        elif comprimento <= 11.0:
            qtd_luzes = 4
        elif comprimento <= 13.5:
            qtd_luzes = 5
        elif comprimento <= 16.0:
            qtd_luzes = 6
        elif comprimento <= 19.0:
            qtd_luzes = 7
        else:  # > 19m
            qtd_luzes = 7  # Manter máximo de 7 luzes
        
        # 4. Buscar e adicionar produto de iluminação
        luz_product = self._get_product_by_name_pattern(luz_name)
        if luz_product:
            products[f"iluminacao_{luz_product['id']}"] = {
                'name': luz_product['name'],
                'price': luz_product['base_price'],
                'quantity': qtd_luzes,
                'unit': luz_product['unit'],
                'item_type': 'incluido',
                'reasoning': f"Iluminação para piscina {comprimento}x{largura}m ({tipo_luzes})",
                'can_change_type': True
            }
        
        return products
    
    def _get_product_by_name_pattern(self, pattern: str) -> Dict:
        """Busca produto por padrão no nome"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Tentar busca exata primeiro
        cursor.execute("""
            SELECT p.*, pc.name as category_name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.name = ? AND p.is_active = 1
            LIMIT 1
        """, (pattern,))
        
        result = cursor.fetchone()
        
        # Se não encontrar exato, tentar busca por padrão
        if not result:
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.name LIKE ? AND p.is_active = 1
                LIMIT 1
            """, (f"%{pattern}%",))
            
            result = cursor.fetchone()
        
        # Debug: mostrar produtos encontrados se não houver resultado
        if not result:
            print(f"⚠️  Produto não encontrado: '{pattern}'")
            cursor.execute("""
                SELECT p.name FROM products p WHERE p.is_active = 1 AND p.name LIKE ?
                LIMIT 5
            """, (f"%{pattern.split()[0]}%",))
            similar = cursor.fetchall()
            if similar:
                print(f"   Produtos similares encontrados:")
                for s in similar:
                    print(f"   - {s[0]}")
        
        conn.close()
        
        if result:
            product = dict(result)
            product['attributes'] = self.db.get_product_attributes(product['id'])
            return product
        
        return None
