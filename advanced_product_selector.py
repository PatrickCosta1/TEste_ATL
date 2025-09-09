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
        # Calcular multiplicador final (novo sistema sem factor de acesso)
        final_multiplier = self.calculator.calculate_final_multiplier(answers, dimensions)
        # Obter breakdown detalhado dos multiplicadores
        multiplier_breakdown = self.calculator.get_multiplier_breakdown(answers, dimensions)
        # Calcular custos específicos de transporte de areia (substitui multiplicador de acesso)
        transport_costs = self.calculator.calculate_transport_costs(answers, metrics)
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
                'multiplier_breakdown': multiplier_breakdown,
                'transport_costs': transport_costs  # Adicionar custos de transporte
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
                        if melhor_inverclear is None:
                            melhor_inverclear = produto
                        else:
                            # Verificar capacidade do melhor atual
                            melhor_match = re.search(r'(\d+)m3', melhor_inverclear['name'])
                            if melhor_match and capacidade < int(melhor_match.group(1)):
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
                        if melhor_mr_pure is None:
                            melhor_mr_pure = produto
                        else:
                            # Verificar capacidade do melhor atual
                            melhor_match = re.search(r'(\d+)m3', melhor_mr_pure['name'])
                            if melhor_match and capacidade < int(melhor_match.group(1)):
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
                        if melhor_mr_pure is None:
                            melhor_mr_pure = produto
                        else:
                            # Verificar capacidade do melhor atual
                            melhor_match = re.search(r'(\d+)m3', melhor_mr_pure['name'])
                            if melhor_match and capacidade < int(melhor_match.group(1)):
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
                        if melhor_uv is None:
                            melhor_uv = produto
                        else:
                            # Verificar capacidade do melhor atual
                            melhor_match = re.search(r'(\d+)m3/h', melhor_uv['name'])
                            if melhor_match and capacidade < int(melhor_match.group(1)):
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
        
        elif revestimento_tipo == 'ceramica':
            # --- Lógica para revestimento cerâmico ---
            revestimento_produtos = self.db.get_products_by_family('Revestimento')
            ceramicos = [p for p in revestimento_produtos if p.get('category_name') == 'Cerâmica']
            quantidades = answers.get('quantidades', {})
            
            # Produto fixo: Impermeabilização
            impermeabilizacao = next((p for p in ceramicos if 'impermeabilização' in p['name'].lower() or 'imper' in p['code'].lower()), None)
            if impermeabilizacao:
                # Usar as áreas já calculadas no metrics
                area_paredes = metrics.get('m2_paredes', 0)
                area_fundo = metrics.get('m2_fundo', 0) 
                area_total = area_paredes + area_fundo
                
                key_imper = "impermeabilizacao_ceramico"
                q_override = quantidades.get(key_imper)
                revestimento[key_imper] = {
                    'name': impermeabilizacao['name'],
                    'price': impermeabilizacao['base_price'],
                    'quantity': float(q_override) if q_override is not None else round(area_total, 2),
                    'unit': impermeabilizacao['unit'],
                    'item_type': 'incluido',
                    'reasoning': f'Impermeabilização cerâmica: {round(area_total, 2)} m² ({area_paredes}m² paredes + {area_fundo}m² fundo)',
                    'can_change_type': True,
                    'editable_price': True,  # Preço editável
                    'editable_cost': True,   # Custo editável
                    'alternatives': [],
                    'product_id': impermeabilizacao['id']
                }
            
            # Produto variável: Item personalizado
            item_personalizado = next((p for p in ceramicos if 'personalizado' in p['name'].lower() or 'custom' in p['code'].lower()), None)
            if item_personalizado:
                # Usar a mesma quantidade da impermeabilização
                area_paredes = metrics.get('m2_paredes', 0)
                area_fundo = metrics.get('m2_fundo', 0) 
                area_total = area_paredes + area_fundo
                
                key_custom = "item_ceramico_personalizado"
                q_override = quantidades.get(key_custom)
                revestimento[key_custom] = {
                    'name': item_personalizado['name'],
                    'price': item_personalizado['base_price'],
                    'quantity': float(q_override) if q_override is not None else round(area_total, 2),
                    'unit': item_personalizado['unit'],
                    'item_type': 'incluido',
                    'reasoning': f'Item personalizável para revestimento cerâmico: {round(area_total, 2)} m² (mesma quantidade da impermeabilização)',
                    'can_change_type': True,
                    'editable_name': True,   # Nome editável
                    'editable_price': True,  # Preço editável
                    'editable_cost': True,   # Custo editável
                    'alternatives': [],
                    'product_id': item_personalizado['id']
                }

        # Selecionar produtos de aquecimento
        aquecimento = self._select_heating_products(conditions, dimensions, metrics)

        # Selecionar produtos de construção da piscina
        construcao = self._select_construction_products(conditions, dimensions, metrics, answers)

        # Selecionar produtos de construção da laje
        construcao_laje = self._select_laje_products(answers, dimensions)

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

            # Verificar se prev_index é válido
            if prev_index is None:
                return family_dict

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
        # Map internal family keys to human-friendly display names so the output
        # contains readable keys (e.g. 'Filtração') and tests/consumers can find them.
        family_display_map = {
            'filtracao': 'Filtração',
            'recirculacao_iluminacao': 'Recirculação e Iluminação',
            'tratamento_agua': 'Tratamento de Água',
            'revestimento': 'Revestimento',
            'aquecimento': 'Aquecimento',
            'construcao': 'Construção da Piscina',
            'construcao_laje': 'Construção da Laje'
        }

        # Para cada família interna, aplicar swap se necessário e manter a chave interna
        for fam_name, fam_dict in [('filtracao', filtracao_sorted), ('recirculacao_iluminacao', recirculacao_sorted), ('tratamento_agua', tratamento_agua), ('revestimento', revestimento), ('aquecimento', aquecimento), ('construcao', construcao), ('construcao_laje', construcao_laje)]:
            if fam_dict:
                selected_key = None
                previous_key = None
                # Exemplo: answers['revestimento_selected'] e answers['revestimento_previous']
                if f'{fam_name}_selected' in answers and f'{fam_name}_previous' in answers:
                    selected_key = answers[f'{fam_name}_selected']
                    previous_key = answers[f'{fam_name}_previous']
                # Usar a chave interna (fam_name) no budget; o frontend/serializador pode mapear para exibição
                families_ordered[fam_name] = swap_item_preserve_quantity_and_position(fam_dict, selected_key, previous_key)
        # Expor também o mapa de exibição para uso posterior pelo frontend/templates
        budget['family_display_map'] = family_display_map
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
        
        # Total dos produtos
        subtotal_products = sum(budget['family_totals'].values())
        
        # Adicionar custos de transporte de areia ao total final
        transport_cost = transport_costs.get('custo_total', 0)
        budget['transport_cost'] = transport_cost
        budget['subtotal_products'] = round(subtotal_products, 2)
        
        # Total geral (produtos + transporte)
        budget['total_price'] = round(subtotal_products + transport_cost, 2)
        
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
        
        import math
        # Restore flat list behavior expected by UI, but skip duplicate product_ids
        seen_product_ids = set()
        main_pump_id = None
        for i, pump in enumerate(suitable_pumps):
            item_type = pump.get('item_type', 'incluido')
            # Calcular quantidade necessária com base na capacidade da bomba
            cap = pump.get('capacity_value', 0) or 0
            if cap > 0:
                quantity = math.ceil(m3_h / cap) if m3_h > 0 else (0 if item_type == 'opcional' else 1)
                # Opcional = default 0 até o usuário selecionar
                if item_type == 'opcional':
                    quantity = 0
            else:
                quantity = 0 if item_type == 'opcional' else 1

            # Garantir pelo menos 1 para itens não-opcionais
            if item_type != 'opcional' and quantity < 1:
                quantity = 1

            # Sufixo no nome baseado no tipo
            name_suffix = ''
            if item_type == 'opcional':
                name_suffix = ' (OPCIONAL)'
            elif item_type == 'alternativo':
                name_suffix = ' (ALTERNATIVO)'

            # Usar numeração sequencial para manter ordem
            pump_key = f"pump_{i+1:02d}_{pump['id']}"

            # Se é a primeira bomba, é a principal
            if main_pump_id is None and item_type == 'incluido':
                main_pump_id = pump_key
            if main_pump_id is None and i == 0:
                main_pump_id = pump_key

            # Skip duplicates by product_id
            pid = pump.get('id')
            if pid is not None and pid in seen_product_ids:
                continue

            pump_data = {
                'name': pump['name'] + name_suffix,
                'price': pump['base_price'],
                'quantity': quantity,
                'unit': pump['unit'],
                'item_type': item_type,
                'reasoning': pump.get('reasoning', f'Bomba selecionada para {m3_h} m³/h - {power_type}'),
                'can_change_type': True,
                'product_id': pid
            }

            # Se é alternativo e temos bomba principal, linkar
            if item_type == 'alternativo' and main_pump_id:
                pump_data['alternative_to'] = main_pump_id

            products[pump_key] = pump_data
            if pid is not None:
                seen_product_ids.add(pid)
        
        # VÁLVULAS - LÓGICA COMPLETA IMPLEMENTADA  
        valve_products = self._get_suitable_valves(conditions['domotics'])
        seen_valve_ids = set()
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

            # Determine main valve
            if main_valve_key is None and item_type == 'incluido':
                main_valve_key = valve_key
            if main_valve_key is None and i == 0:
                main_valve_key = valve_key

            # Skip duplicates by product_id
            vid = valve.get('id')
            if vid is not None and vid in seen_valve_ids:
                continue

            valve_data = {
                'name': valve['name'] + name_suffix,
                'price': valve['base_price'],
                'quantity': quantity,
                'unit': valve['unit'],
                'item_type': item_type,
                'reasoning': valve.get('reasoning', 'Válvula selecionada automaticamente'),
                'can_change_type': True,
                'product_id': vid
            }
            # Se for alternativo, garantir que alternative_to aponte para a principal
            if item_type == 'alternativo' and main_valve_key:
                valve_data['alternative_to'] = main_valve_key

            products[valve_key] = valve_data
            if vid is not None:
                seen_valve_ids.add(vid)
        
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
                'can_change_type': True,  # Permitir troca de filtro
                'product_id': best_filter.get('id')
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
                        'can_change_type': False,
                        'product_id': vidro_fino.get('id')
                    }
                    products[areia_key] = {
                        'name': areia_fina['name'],
                        'price': areia_fina['base_price'],
                        'quantity': n_sacos_areia_fina,
                        'unit': areia_fina['unit'],
                        'item_type': 'alternativo',
                        'reasoning': f"Alternativa ao vidro filtrante fino: {n_sacos_areia_fina} sacos (areia fina)",
                        'alternative_to': vidro_key,
                        'can_change_type': False,
                        'product_id': areia_fina.get('id')
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
                        'can_change_type': False,
                        'product_id': vidro_grosso.get('id')
                    }
                    products[areia_key] = {
                        'name': areia_grossa['name'],
                        'price': areia_grossa['base_price'],
                        'quantity': n_sacos_areia_grossa,
                        'unit': areia_grossa['unit'],
                        'item_type': 'alternativo',
                        'reasoning': f"Alternativa ao vidro filtrante grosso: {n_sacos_areia_grossa} sacos (areia grossa)",
                        'alternative_to': vidro_key,
                        'can_change_type': False,
                        'product_id': areia_grossa.get('id')
                    }

        # Corrigir agrupamento visual dos alternativos da válvula (garantia extra)
        # Após todos os produtos montados, garantir que toda válvula alternativa aponte para a principal
        if main_valve_key:
            for k, v in products.items():
                if v.get('item_type') == 'alternativo' and 'Válvula' in v.get('name', ''):
                    v['alternative_to'] = main_valve_key

        # --- Remover possíveis duplicados ---
        # Priorizar deduplicação por product_id quando disponível.
        # Caso não haja product_id (itens criados manualmente), deduplicar por assinatura
        # (name, price, unit, item_type).
        seen_ids = set()
        seen_sigs = set()
        deduped = {}
        for k, v in products.items():
            pid = v.get('product_id')
            # construir assinatura
            sig = (v.get('name'),
                   float(v.get('price')) if isinstance(v.get('price'), (int, float)) else v.get('price'),
                   v.get('unit'),
                   v.get('item_type'))

            if pid is not None:
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
            else:
                if sig in seen_sigs:
                    continue
                seen_sigs.add(sig)

            deduped[k] = v

        return deduped
    
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
        valves = []
        # 1) Tentar obter category_id a partir do DB diretamente
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM product_categories WHERE name = ? LIMIT 1", ("Válvulas Seletoras",))
            row = cursor.fetchone()
            conn.close()
            if row:
                cat_id = row['id']
                valves = self.db.get_products_by_category(cat_id)
            else:
                valves = []
        except Exception as e:
            print(f"[Fallback] Erro ao buscar categoria de válvulas no BD: {e}")
            valves = []

        # 2) Se não encontrou no DB, usar fallback a partir de default_data.py
        if not valves:
            try:
                from default_data import products, product_categories
            except ImportError:
                products = globals().get('products', [])
                product_categories = globals().get('product_categories', [])
            valvulas_cat = next((c for c in product_categories if c['name'] == 'Válvulas Seletoras'), None)
            if valvulas_cat:
                for prod in products:
                    if prod.get('category_id') == valvulas_cat['id'] and prod.get('is_active', 1):
                        prod_copy = prod.copy()
                        prod_copy['category_name'] = 'Válvulas Seletoras'
                        prod_copy['attributes'] = self.db.get_product_attributes(prod['id'])
                        valves.append(prod_copy)

        # Separar válvulas por tipo
        manual_valves = [v for v in valves if 'manual' in v['name'].lower()]
        auto_valves = [v for v in valves if 'iwash' in v['name'].lower() or 'automática' in v['name'].lower() or 'automatica' in v['name'].lower()]

        result = []

        if has_domotics == 'true':
            # COM DOMÓTICA: Automática INCLUÍDA por padrão, Manual ALTERNATIVA
            if auto_valves:
                for valve in auto_valves:
                    valve['item_type'] = 'incluido'
                    valve['reasoning'] = 'Válvula automática para integração domótica'
                    result.append(valve)
                for valve in manual_valves:
                    valve['item_type'] = 'alternativo'
                    valve['reasoning'] = 'Alternativa manual'
                    result.append(valve)
            else:
                # fallback: se não houver automática, incluir manual como principal
                for valve in manual_valves:
                    valve['item_type'] = 'incluido'
                    valve['reasoning'] = 'Válvula manual padrão (sem automática disponível)'
                    result.append(valve)
        else:
            # SEM DOMÓTICA: Manual INCLUÍDA por padrão, Automática ALTERNATIVA
            if manual_valves:
                for valve in manual_valves:
                    valve['item_type'] = 'incluido'
                    valve['reasoning'] = 'Válvula manual padrão'
                    result.append(valve)
                for valve in auto_valves:
                    valve['item_type'] = 'alternativo'
                    valve['reasoning'] = 'Upgrade automático alternativo'
                    result.append(valve)
            else:
                # fallback: se não houver manual, incluir automática como principal
                for valve in auto_valves:
                    valve['item_type'] = 'incluido'
                    valve['reasoning'] = 'Válvula automática (sem manual disponível)'
                    result.append(valve)

        return result
    
    def _get_suitable_pumps(self, required_m3_h: float, power_type: str) -> List[Dict]:
        """Seleciona bombas baseado na capacidade e tipo de energia - COM VELOCIDADE VARIÁVEL"""
        
        pumps = []
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                JOIN product_categories pc ON p.category_id = pc.id
                WHERE pc.name = 'Bomba de Filtração' AND p.is_active = 1
                ORDER BY p.base_price
            """)
            for row in cursor.fetchall():
                pump = dict(row)
                pump['attributes'] = self.db.get_product_attributes(pump['id'])
                pumps.append(pump)
            conn.close()
            # If DB returned no active pump products, fall back to default_data
            if not pumps:
                try:
                    from default_data import products, product_categories, product_attributes, attribute_types
                except ImportError:
                    products = globals().get('products', [])
                    product_categories = globals().get('product_categories', [])
                    product_attributes = globals().get('product_attributes', [])
                    attribute_types = globals().get('attribute_types', [])

                pump_cat_ids = [c['id'] for c in product_categories if 'bomba' in c['name'].lower()]
                if not pump_cat_ids:
                    bombas_cat = next((c for c in product_categories if c['name'] == 'Bomba de Filtração'), None)
                    pump_cat_ids = [bombas_cat['id']] if bombas_cat else []

                for prod in products:
                    if prod.get('category_id') in pump_cat_ids and prod.get('is_active', 1):
                        prod_copy = prod.copy()
                        cat = next((c for c in product_categories if c['id'] == prod['category_id']), None)
                        prod_copy['category_name'] = cat['name'] if cat else 'Bomba de Filtração'
                        attrs = {}
                        for pa in product_attributes:
                            if pa['product_id'] != prod['id']:
                                continue
                            at = next((a for a in attribute_types if a['id'] == pa['attribute_type_id']), None)
                            if not at:
                                continue
                            name = at['name']
                            dt = at['data_type']
                            if dt == 'numeric':
                                attrs[name] = {'value': pa.get('value_numeric'), 'unit': at.get('unit')}
                            elif dt == 'boolean':
                                attrs[name] = bool(pa.get('value_boolean'))
                            else:
                                attrs[name] = pa.get('value_text')
                        prod_copy['attributes'] = attrs
                        pumps.append(prod_copy)
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD para bombas: {e}")
            try:
                from default_data import products, product_categories, product_attributes, attribute_types
            except ImportError:
                products = globals().get('products', [])
                product_categories = globals().get('product_categories', [])
                product_attributes = globals().get('product_attributes', [])
                attribute_types = globals().get('attribute_types', [])

            # Collect categories that look like pump categories (robust to naming differences)
            pump_cat_ids = [c['id'] for c in product_categories if 'bomba' in c['name'].lower()]
            if not pump_cat_ids:
                bombas_cat = next((c for c in product_categories if c['name'] == 'Bomba de Filtração'), None)
                pump_cat_ids = [bombas_cat['id']] if bombas_cat else []

            for prod in products:
                if prod.get('category_id') in pump_cat_ids and prod.get('is_active', 1):
                    prod_copy = prod.copy()
                    cat = next((c for c in product_categories if c['id'] == prod['category_id']), None)
                    prod_copy['category_name'] = cat['name'] if cat else 'Bomba de Filtração'

                    # Build attributes from fallback product_attributes / attribute_types
                    attrs = {}
                    for pa in product_attributes:
                        if pa['product_id'] != prod['id']:
                            continue
                        at = next((a for a in attribute_types if a['id'] == pa['attribute_type_id']), None)
                        if not at:
                            continue
                        name = at['name']
                        dt = at['data_type']
                        if dt == 'numeric':
                            attrs[name] = {'value': pa.get('value_numeric'), 'unit': at.get('unit')}
                        elif dt == 'boolean':
                            attrs[name] = bool(pa.get('value_boolean'))
                        else:
                            attrs[name] = pa.get('value_text')

                    prod_copy['attributes'] = attrs
                    pumps.append(prod_copy)
        
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
    
    def _get_product_by_name_pattern(self, pattern: str) -> dict | None:
        """Busca produto por padrão no nome, com fallback para dados Python se BD falhar"""
        try:
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
            if result:
                product = dict(result)
                product['attributes'] = self.db.get_product_attributes(product['id'])
                conn.close()
                return product
            conn.close()
        except Exception as e:
            print(f"[Fallback] Erro ao acessar BD: {e}")

        # Fallback para dados Python
        try:
            from default_data import products, product_categories
        except ImportError:
            products = globals().get('products', [])
            product_categories = globals().get('product_categories', [])

        # Busca exata
        for prod in products:
            if prod.get('is_active', 1) and prod['name'] == pattern:
                cat = next((c for c in product_categories if c['id'] == prod['category_id']), None)
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat['name'] if cat else None
                prod_copy['attributes'] = self.db.get_product_attributes(prod['id'])
                return prod_copy
        # Busca por padrão
        for prod in products:
            if prod.get('is_active', 1) and pattern.lower() in prod['name'].lower():
                cat = next((c for c in product_categories if c['id'] == prod['category_id']), None)
                prod_copy = prod.copy()
                prod_copy['category_name'] = cat['name'] if cat else None
                prod_copy['attributes'] = self.db.get_product_attributes(prod['id'])
                return prod_copy
        print(f"⚠️  Produto não encontrado: '{pattern}' (fallback)")
        # Sugestão de similares
        similar = [p['name'] for p in products if pattern.split()[0].lower() in p['name'].lower()][:5]
        if similar:
            print(f"   Produtos similares encontrados:")
            for s in similar:
                print(f"   - {s}")
        return None

    def _select_heating_products(self, conditions: Dict, dimensions: Dict, metrics: Dict) -> Dict:
        """Seleciona produtos de aquecimento baseado no volume da piscina"""
        aquecimento = {}
        
        # Obter volume da piscina
        volume_m3 = dimensions.get('volume', 0) or metrics.get('volume', 0) or 0
        
        if volume_m3 <= 0:
            return aquecimento
        
        # Buscar produtos da família Aquecimento
        heating_products = self.db.get_products_by_family('Aquecimento')
        
        if not heating_products:
            # Fallback para default_data se DB não tiver produtos
            try:
                from default_data import products, product_categories
                aquecimento_cat = next((c for c in product_categories if c['name'] == 'Aquecimento'), None)
                if aquecimento_cat:
                    heating_products = []
                    for prod in products:
                        if prod.get('category_id') == 27 and prod.get('is_active', 1):  # ID 27 = Bomba de Calor
                            prod_copy = prod.copy()
                            prod_copy['category_name'] = 'Bomba de Calor'
                            heating_products.append(prod_copy)
            except ImportError:
                return aquecimento
        
        # Filtrar produtos da categoria "Bomba de Calor"
        heat_pumps = [p for p in heating_products if 'bomba de calor' in (p.get('category_name', '') or '').lower()]
        
        if not heat_pumps:
            return aquecimento
        
        # Separar bombas por marca
        mr_comfort_pumps = [p for p in heat_pumps if 'mr. comfort' in p.get('brand', '').lower()]
        fairland_pumps = [p for p in heat_pumps if 'fairland' in p.get('brand', '').lower()]
        
        # Mapear produtos Mr. Comfort por volume ideal (preferência por eficiência)
        mr_comfort_specs = [
            {'model': '90M', 'kw': 9, 'min_volume': 20, 'max_volume': 50, 'optimal': 35},
            {'model': '130M', 'kw': 12.6, 'min_volume': 30, 'max_volume': 60, 'optimal': 45},
            {'model': '160M', 'kw': 16.1, 'min_volume': 40, 'max_volume': 75, 'optimal': 57.5},
            {'model': '200M', 'kw': 20.0, 'min_volume': 50, 'max_volume': 90, 'optimal': 70},
            {'model': '240M', 'kw': 24.0, 'min_volume': 60, 'max_volume': 110, 'optimal': 85}
        ]
        
        # Mapear produtos Fairland InverX20 por volume ideal (gama superior)
        fairland_specs = [
            {'model': 'X20-14', 'kw': 14, 'min_volume': 30, 'max_volume': 50, 'optimal': 40},
            {'model': 'X20-18', 'kw': 18, 'min_volume': 40, 'max_volume': 65, 'optimal': 52.5},
            {'model': 'X20-22', 'kw': 22, 'min_volume': 45, 'max_volume': 75, 'optimal': 60},
            {'model': 'X20-26', 'kw': 26, 'min_volume': 55, 'max_volume': 90, 'optimal': 72.5}
        ]
        
        # Selecionar a bomba Mr. Comfort adequada (incluída por padrão)
        selected_mr_comfort = None
        selected_mr_spec = None
        
        # Encontrar todos os modelos Mr. Comfort válidos para o volume
        valid_mr_specs = [spec for spec in mr_comfort_specs if spec['min_volume'] <= volume_m3 <= spec['max_volume']]
        
        if valid_mr_specs:
            # Se há modelos válidos, escolher o mais próximo do volume ótimo
            selected_mr_spec = min(valid_mr_specs, key=lambda x: abs(volume_m3 - x['optimal']))
            selected_mr_comfort = next((p for p in mr_comfort_pumps if selected_mr_spec['model'] in p['name']), None)
        else:
            # Se não há modelos na faixa, escolher o mais próximo
            if volume_m3 < 20:  # Muito baixo, selecionar o menor
                selected_mr_spec = mr_comfort_specs[0]
            elif volume_m3 > 110:  # Muito alto, selecionar o maior
                selected_mr_spec = mr_comfort_specs[-1]
            else:
                # Encontrar o mais próximo baseado na distância dos limites
                best_spec = None
                min_distance = float('inf')
                
                for spec in mr_comfort_specs:
                    # Calcular distância até a faixa de operação
                    if volume_m3 < spec['min_volume']:
                        distance = spec['min_volume'] - volume_m3
                    else:  # volume_m3 > spec['max_volume']
                        distance = volume_m3 - spec['max_volume']
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_spec = spec
                
                selected_mr_spec = best_spec
            
            if selected_mr_spec:
                selected_mr_comfort = next((p for p in mr_comfort_pumps if selected_mr_spec['model'] in p['name']), None)
        
        # Incluir a bomba Mr. Comfort selecionada
        if selected_mr_comfort:
            aquecimento[f"bomba_calor_{selected_mr_comfort['id']}"] = {
                'name': selected_mr_comfort['name'],
                'price': selected_mr_comfort['base_price'],
                'quantity': 1,
                'unit': selected_mr_comfort['unit'],
                'item_type': 'incluido',
                'reasoning': f'Bomba de calor selecionada para piscina de {volume_m3} m³',
                'can_change_type': True,
                'editable_price': False,
                'editable_name': False
            }
        
        # Selecionar bomba Fairland equivalente como opcional (gama superior)
        selected_fairland = None
        
        # Encontrar bomba Fairland adequada baseada no volume
        valid_fairland_specs = [spec for spec in fairland_specs if spec['min_volume'] <= volume_m3 <= spec['max_volume']]
        
        if valid_fairland_specs:
            # Escolher a Fairland mais adequada para o volume
            selected_fairland_spec = min(valid_fairland_specs, key=lambda x: abs(volume_m3 - x['optimal']))
            selected_fairland = next((p for p in fairland_pumps if selected_fairland_spec['model'] in p['name']), None)
        else:
            # Fallback: se o volume está fora das faixas Fairland, escolher a mais próxima
            if volume_m3 < 30:  # Menor que o mínimo Fairland
                selected_fairland_spec = fairland_specs[0]  # X20-14
            elif volume_m3 > 90:  # Maior que o máximo Fairland
                selected_fairland_spec = fairland_specs[-1]  # X20-26
            else:
                # Encontrar a mais próxima
                best_fairland_spec = None
                min_distance = float('inf')
                
                for spec in fairland_specs:
                    if volume_m3 < spec['min_volume']:
                        distance = spec['min_volume'] - volume_m3
                    else:  # volume_m3 > spec['max_volume']
                        distance = volume_m3 - spec['max_volume']
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_fairland_spec = spec
                
                selected_fairland_spec = best_fairland_spec
            
            if selected_fairland_spec:
                selected_fairland = next((p for p in fairland_pumps if selected_fairland_spec['model'] in p['name']), None)
        
        # Incluir a bomba Fairland como alternativa (gama superior)
        if selected_fairland and selected_mr_comfort:
            main_mr_key = f"bomba_calor_{selected_mr_comfort['id']}"
            aquecimento[f"bomba_calor_fairland_{selected_fairland['id']}"] = {
                'name': selected_fairland['name'],
                'price': selected_fairland['base_price'],
                'quantity': 1,
                'unit': selected_fairland['unit'],
                'item_type': 'alternativo',
                'alternative_to': main_mr_key,
                'reasoning': f'Bomba de calor Fairland - Gama Superior alternativa para piscina de {volume_m3} m³',
                'can_change_type': True,
                'editable_price': False,
                'editable_name': False
            }
        
        return aquecimento

    def _select_construction_products(self, conditions: Dict, dimensions: Dict, metrics: Dict, answers: Dict) -> Dict:
        """Seleciona produtos de construção da piscina com preços regionais"""
        import math
        
        construcao = {}
        
        # Obter localidade dos answers primeiro, depois client_data como fallback
        localidade = answers.get('localidade', '')
        if not localidade:
            client_data = {}
            if session:
                budget = session.get('current_budget', {})
                client_data = budget.get('client_data', {})
            localidade = client_data.get('localidade', '')
        
        if localidade == 'Outro':
            localidade_outro = answers.get('localidade_outro', '')
            if not localidade_outro and session:
                budget = session.get('current_budget', {})
                client_data = budget.get('client_data', {})
                localidade_outro = client_data.get('localidade_outro', '')
            localidade = localidade_outro
        
        # Mapeamento de localidades para regiões de preços
        regiao_precos = {
            'Viseu': {
                'Bloco Cofragem 50x20x20': 0.90, 'Bloco Normal 50x20x20': 0.83, 'Cimento Cimpor 32,5R': 4.03,
                'Malha Eletrosoldada 6mm': 2.96, 'Heliaço 10mm 6m': 3.28, 'Meia Areia': 25.00,
                'Mistura': 22.00, 'Brita nº2': 28.70, 'Reboco Exterior Cinza': 2.60,
                'Viga': 2.30, 'Abobadilhas 40cm': 0.71
            },
            'Ponte Lima': {
                'Bloco Cofragem 50x20x20': 0.92, 'Bloco Normal 50x20x20': 0.88, 'Cimento Cimpor 32,5R': 3.85,
                'Malha Eletrosoldada 6mm': 2.07, 'Heliaço 10mm 6m': 3.29, 'Meia Areia': 25.00,
                'Mistura': 26.25, 'Brita nº2': 25.00, 'Reboco Exterior Cinza': 2.91,
                'Viga': 2.08, 'Abobadilhas 40cm': 0.66
            },
            'Barcelos': {
                'Bloco Cofragem 50x20x20': 0.85, 'Bloco Normal 50x20x20': 0.74, 'Cimento Cimpor 32,5R': 3.98,
                'Malha Eletrosoldada 6mm': 1.90, 'Heliaço 10mm 6m': 2.94, 'Meia Areia': 24.39,
                'Mistura': 32.52, 'Brita nº2': 24.39, 'Reboco Exterior Cinza': 2.85,
                'Viga': 1.98, 'Abobadilhas 40cm': 0.63
            },
            'Santa Maria da Feira': {
                'Bloco Cofragem 50x20x20': 1.12, 'Bloco Normal 50x20x20': 0.95, 'Cimento Cimpor 32,5R': 3.63,
                'Malha Eletrosoldada 6mm': 2.66, 'Heliaço 10mm 6m': 3.30, 'Meia Areia': 34.00,
                'Mistura': 31.00, 'Brita nº2': 31.00, 'Reboco Exterior Cinza': 2.30,
                'Viga': 3.00, 'Abobadilhas 40cm': 0.60
            },
            'Póvoa de Varzim/Vila do Conde': {
                'Bloco Cofragem 50x20x20': 1.09, 'Bloco Normal 50x20x20': 0.85, 'Cimento Cimpor 32,5R': 3.98,
                'Malha Eletrosoldada 6mm': 2.78, 'Heliaço 10mm 6m': 3.77, 'Meia Areia': 27.14,
                'Mistura': 27.14, 'Brita nº2': 27.14, 'Reboco Exterior Cinza': 2.70,
                'Viga': 2.30, 'Abobadilhas 40cm': 0.71
            },
            'Viana do Castelo': {
                'Bloco Cofragem 50x20x20': 1.05, 'Bloco Normal 50x20x20': 0.90, 'Cimento Cimpor 32,5R': 3.95,
                'Malha Eletrosoldada 6mm': 2.27, 'Heliaço 10mm 6m': 3.70, 'Meia Areia': 26.00,
                'Mistura': 33.50, 'Brita nº2': 26.00, 'Reboco Exterior Cinza': 3.00,
                'Viga': 2.67, 'Abobadilhas 40cm': 0.58
            },
            'Famalicão': {
                'Bloco Cofragem 50x20x20': 1.12, 'Bloco Normal 50x20x20': 0.98, 'Cimento Cimpor 32,5R': 3.62,
                'Malha Eletrosoldada 6mm': 1.89, 'Heliaço 10mm 6m': 3.47, 'Meia Areia': 39.27,
                'Mistura': 37.55, 'Brita nº2': 37.55, 'Reboco Exterior Cinza': 2.73,
                'Viga': 2.30, 'Abobadilhas 40cm': 0.70
            },
            'Ovar/Estarreja': {
                'Bloco Cofragem 50x20x20': 1.34, 'Bloco Normal 50x20x20': 1.10, 'Cimento Cimpor 32,5R': 3.84,
                'Malha Eletrosoldada 6mm': 2.72, 'Heliaço 10mm 6m': 3.94, 'Meia Areia': 27.24,
                'Mistura': 27.74, 'Brita nº2': 27.24, 'Reboco Exterior Cinza': 3.25,
                'Viga': 3.00, 'Abobadilhas 40cm': 0.70
            },
            'Gaia': {
                'Bloco Cofragem 50x20x20': 1.32, 'Bloco Normal 50x20x20': 1.10, 'Cimento Cimpor 32,5R': 3.78,
                'Malha Eletrosoldada 6mm': 3.39, 'Heliaço 10mm 6m': 3.80, 'Meia Areia': 35.00,
                'Mistura': 35.00, 'Brita nº2': 35.00, 'Reboco Exterior Cinza': 2.08,
                'Viga': 3.75, 'Abobadilhas 40cm': 0.68
            },
            'Braga': {
                'Bloco Cofragem 50x20x20': 1.13, 'Bloco Normal 50x20x20': 0.89, 'Cimento Cimpor 32,5R': 3.90,
                'Malha Eletrosoldada 6mm': 3.36, 'Heliaço 10mm 6m': 4.50, 'Meia Areia': 27.50,
                'Mistura': 27.50, 'Brita nº2': 27.50, 'Reboco Exterior Cinza': 2.92,
                'Viga': 3.25, 'Abobadilhas 40cm': 0.73
            },
            'Guimarães': {
                'Bloco Cofragem 50x20x20': 1.08, 'Bloco Normal 50x20x20': 0.95, 'Cimento Cimpor 32,5R': 4.01,
                'Malha Eletrosoldada 6mm': 3.36, 'Heliaço 10mm 6m': 3.70, 'Meia Areia': 35.00,
                'Mistura': 35.00, 'Brita nº2': 34.00, 'Reboco Exterior Cinza': 2.70,
                'Viga': 2.30, 'Abobadilhas 40cm': 0.75
            },
            'Porto/Maia/Matosinhos': {
                'Bloco Cofragem 50x20x20': 1.32, 'Bloco Normal 50x20x20': 1.10, 'Cimento Cimpor 32,5R': 3.78,
                'Malha Eletrosoldada 6mm': 3.39, 'Heliaço 10mm 6m': 3.80, 'Meia Areia': 35.00,
                'Mistura': 35.00, 'Brita nº2': 35.00, 'Reboco Exterior Cinza': 2.08,
                'Viga': 3.75, 'Abobadilhas 40cm': 0.68
            }
        }
        
        # Mapeamento de localidades individuais para grupos de preços
        # Permite que localidades separadas usem a mesma tabela de preços
        mapeamento_localidades = {
            # Póvoa de Varzim e Vila do Conde usam os mesmos preços
            'Póvoa de Varzim': 'Póvoa de Varzim/Vila do Conde',
            'Vila do Conde': 'Póvoa de Varzim/Vila do Conde',
            
            # Ovar e Estarreja usam os mesmos preços
            'Ovar': 'Ovar/Estarreja',
            'Estarreja': 'Ovar/Estarreja',
            
            # Porto, Maia e Matosinhos usam os mesmos preços
            'Porto': 'Porto/Maia/Matosinhos',
            'Maia': 'Porto/Maia/Matosinhos',
            'Matosinhos': 'Porto/Maia/Matosinhos'
        }
        
        # Obter preços para a localidade específica ou calcular média se for "Outro"
        def get_price_for_region(product_name):
            # Verificar se a localidade precisa ser mapeada para um grupo
            localidade_para_preco = mapeamento_localidades.get(localidade, localidade)
            
            preco_custo = 0
            if localidade_para_preco in regiao_precos:
                preco_custo = regiao_precos[localidade_para_preco].get(product_name, 0)
            else:
                # Calcular média de todas as regiões
                total = 0
                count = 0
                for region_prices in regiao_precos.values():
                    if product_name in region_prices:
                        total += region_prices[product_name]
                        count += 1
                preco_custo = total / count if count > 0 else 0
            
            # CORREÇÃO: Converter preço de custo para preço de venda (× 100/60)
            preco_venda = preco_custo * 100 / 60
            return round(preco_venda, 2)
        
        # Obter métricas calculadas
        m2_paredes = metrics.get('m2_paredes', 0)
        m2_fundo = metrics.get('m2_fundo', 0)
        m3_massa = metrics.get('m3_massa', 0)
        perimetro = metrics.get('perimetro', 0)
        prof_min = dimensions.get('prof_min', 0)
        prof_max = dimensions.get('prof_max', 0)
        prof_media = (prof_min + prof_max) / 2 if prof_min and prof_max else 0
        
        # Zona de praia e escadas
        zona_praia = answers.get('zona_praia', 'nao') == 'sim'
        zona_praia_largura = answers.get('zona_praia_largura', 0)
        # O comprimento da zona de praia é sempre igual à largura da piscina
        zona_praia_comprimento = dimensions.get('largura', 0) if zona_praia else 0
        escadas = answers.get('escadas', 'nao') == 'sim'
        escadas_largura = answers.get('escadas_largura', 0)
        
        # 1. Bloco Cofragem 50x20x20: 10 blocos por m² paredes (arredondar para cima)
        if m2_paredes > 0:
            qty_bloco_cofragem = math.ceil(m2_paredes * 10)
            construcao['bloco_cofragem'] = {
                'name': 'Bloco Cofragem 50x20x20',
                'price': get_price_for_region('Bloco Cofragem 50x20x20'),
                'quantity': qty_bloco_cofragem,
                'unit': 'un',
                'item_type': 'incluido',
                'reasoning': f'10 blocos por m² de parede ({m2_paredes:.2f} m²)',
                'can_change_type': True
            }
        
        # 2. Bloco Normal 50x20x20: só se houver escadas
        if escadas and escadas_largura > 0:
            qty_bloco_normal = math.floor((escadas_largura / 0.2) * ((prof_min - 0.3) / 0.2))
            if qty_bloco_normal > 0:
                construcao['bloco_normal'] = {
                    'name': 'Bloco Normal 50x20x20',
                    'price': get_price_for_region('Bloco Normal 50x20x20'),
                    'quantity': qty_bloco_normal,
                    'unit': 'un',
                    'item_type': 'incluido',
                    'reasoning': f'Para escadas: ({escadas_largura}/0,2) × (({prof_min}-0,3)/0,2)',
                    'can_change_type': True
                }
        
        # 3. Cimento Cimpor 32,5R: 10 sacos por m³ massa
        if m3_massa > 0:
            qty_cimento = m3_massa * 10
            construcao['cimento'] = {
                'name': 'Cimento Cimpor 32,5R',
                'price': get_price_for_region('Cimento Cimpor 32,5R'),
                'quantity': qty_cimento,
                'unit': 'un',
                'item_type': 'incluido',
                'reasoning': f'10 sacos por m³ de massa ({m3_massa:.2f} m³)',
                'can_change_type': True
            }
        
        # 4. Mistura: 1 m³ por m³ massa
        if m3_massa > 0:
            construcao['mistura'] = {
                'name': 'Mistura',
                'price': get_price_for_region('Mistura'),
                'quantity': m3_massa,
                'unit': 'm3',
                'item_type': 'incluido',
                'reasoning': f'1 m³ por m³ de massa ({m3_massa:.2f} m³)',
                'can_change_type': True
            }
        
        # 5. Malha Eletrosoldada 6mm: igual a m² paredes
        if m2_paredes > 0:
            construcao['malha_eletrosoldada'] = {
                'name': 'Malha Eletrosoldada 6mm',
                'price': get_price_for_region('Malha Eletrosoldada 6mm'),
                'quantity': m2_paredes,
                'unit': 'm2',
                'item_type': 'incluido',
                'reasoning': f'Igual a m² de paredes ({m2_paredes:.2f} m²)',
                'can_change_type': True
            }
        
        # 6. Heliaço 10mm 6m: Barras Verticais + Barras Horizontais
        if perimetro > 0 and prof_max > 0:
            # Barras Verticais: (Altura_2m × 2)/6, onde Altura_2m = (Perímetro/0,2)
            altura_2m = perimetro / 0.2
            barras_verticais = (altura_2m * 2) / 6
            
            # Barras Horizontais: (Nº_Fiadas × Perímetro × 2)/6, onde Nº_Fiadas = prof_max/0,2
            n_fiadas = prof_max / 0.2
            barras_horizontais = (n_fiadas * perimetro * 2) / 6
            
            qty_heliaco = math.ceil(barras_verticais + barras_horizontais)
            construcao['heliaco'] = {
                'name': 'Heliaço 10mm 6m',
                'price': get_price_for_region('Heliaço 10mm 6m'),
                'quantity': qty_heliaco,
                'unit': 'un',
                'item_type': 'incluido',
                'reasoning': f'Barras verticais: {barras_verticais:.1f} + Barras horizontais: {barras_horizontais:.1f}',
                'can_change_type': True
            }
        
        # 7. Arame Queimado: sempre 2 kg
        construcao['arame_queimado'] = {
            'name': 'Arame Queimado',
            'price': 2.50,  # Preço fixo
            'quantity': 2,
            'unit': 'kg',
            'item_type': 'incluido',
            'reasoning': 'Quantidade fixa: 2 kg',
            'can_change_type': True
        }
        
        # 8. Meia Areia: sempre 1 m³
        construcao['meia_areia'] = {
            'name': 'Meia Areia',
            'price': get_price_for_region('Meia Areia'),
            'quantity': 1,
            'unit': 'm3',
            'item_type': 'incluido',
            'reasoning': 'Quantidade fixa: 1 m³',
            'can_change_type': True
        }
        
        # 9. Reboco Exterior: 0,6 sacos por m² parede
        if m2_paredes > 0:
            qty_reboco = m2_paredes * 0.6
            construcao['reboco_exterior'] = {
                'name': 'Reboco Exterior Cinza',
                'price': get_price_for_region('Reboco Exterior Cinza'),
                'quantity': qty_reboco,
                'unit': 'un',
                'item_type': 'incluido',
                'reasoning': f'0,6 sacos por m² de parede ({m2_paredes:.2f} m²)',
                'can_change_type': True
            }
        
        # 10. Vigas: só se zona de praia
        if zona_praia and zona_praia_largura > 0 and zona_praia_comprimento > 0:
            n_vigas = ((zona_praia_comprimento / 0.52) + 1) * zona_praia_largura
            construcao['vigas'] = {
                'name': 'Viga',
                'price': get_price_for_region('Viga'),
                'quantity': n_vigas,
                'unit': 'm',
                'item_type': 'incluido',
                'reasoning': f'Zona praia: (({zona_praia_comprimento}/0,52)+1) × {zona_praia_largura}',
                'can_change_type': True
            }
            
            # 11. Abobadilhas: só se zona de praia
            qty_abobadilhas = (zona_praia_largura / 0.40) * n_vigas
            construcao['abobadilhas'] = {
                'name': 'Abobadilhas 40cm',
                'price': get_price_for_region('Abobadilhas 40cm'),
                'quantity': qty_abobadilhas,
                'unit': 'un',
                'item_type': 'incluido',
                'reasoning': f'({zona_praia_largura}/0,40) × {n_vigas:.1f} vigas',
                'can_change_type': True
            }
        
        # 12. Tela Pitonada: perímetro × profundidade média
        if perimetro > 0 and prof_media > 0:
            qty_tela = perimetro * prof_media
            construcao['tela_pitonada'] = {
                'name': 'Tela Pitonada',
                'price': 1.50,  # Preço fixo
                'quantity': qty_tela,
                'unit': 'm2',
                'item_type': 'incluido',
                'reasoning': f'Perímetro × prof. média: {perimetro:.2f} × {prof_media:.2f}',
                'can_change_type': True
            }
        
        # 13. Brita nº2: m² fundo × 0,05 (arredondar para cima)
        if m2_fundo > 0:
            qty_brita = math.ceil(m2_fundo * 0.05)
            construcao['brita_n2'] = {
                'name': 'Brita nº2',
                'price': get_price_for_region('Brita nº2'),
                'quantity': qty_brita,
                'unit': 'm3',
                'item_type': 'incluido',
                'reasoning': f'M² fundo × 0,05: {m2_fundo:.2f} × 0,05 (arredondado)',
                'can_change_type': True
            }
        
        return construcao

    def _select_laje_products(self, answers: Dict, dimensions: Dict) -> Dict:
        """Seleciona produtos de construção da laje baseado nas respostas do questionário"""
        import math
        
        construcao_laje = {}
        
        # Verificar se haverá laje
        havera_laje = answers.get('havera_laje', 'nao')
        if havera_laje != 'sim':
            return construcao_laje
        
        # Obter dados da laje
        try:
            laje_m2 = float(answers.get('laje_m2', 0))
            laje_espessura = float(answers.get('laje_espessura', 0))  # Já em metros (0.10 ou 0.15)
        except (ValueError, TypeError):
            return construcao_laje
        
        if laje_m2 <= 0 or laje_espessura <= 0:
            return construcao_laje
        
        # Converter espessura para centímetros para exibição
        laje_espessura_cm = int(laje_espessura * 100)
        
        # Calcular m³ da laje
        laje_m3 = laje_m2 * laje_espessura
        
        # Definir preços dos materiais de revestimento
        precos_revestimento = {
            'granito_vila_real': 35.0,
            'granito_pedras_salgadas': 35.0,
            'granito_preto_angola': 90.0,
            'granito_preto_zimbabue': 140.0,
            'marmore_branco_ibiza': 90.0,
            'travertino_turco': 90.0,
            'pedra_hijau': 40.0  # cerâmico
        }
        
        # Nomes dos materiais
        nomes_materiais = {
            'granito_vila_real': 'Granito Vila Real',
            'granito_pedras_salgadas': 'Granito Pedras Salgadas',
            'granito_preto_angola': 'Granito Preto Angola',
            'granito_preto_zimbabue': 'Granito Preto Zimbabue',
            'marmore_branco_ibiza': 'Mármore Branco Ibiza',
            'travertino_turco': 'Travertino Turco',
            'pedra_hijau': 'Pedra Hijau'
        }
        
        # Tipos de material (para diferenciação futura)
        tipos_materiais = {
            'granito_vila_real': 'natural',
            'granito_pedras_salgadas': 'natural',
            'granito_preto_angola': 'natural',
            'granito_preto_zimbabue': 'natural',
            'marmore_branco_ibiza': 'natural',
            'travertino_turco': 'natural',
            'pedra_hijau': 'ceramico'
        }
        
        # Item 1: Pavimento térreo
        # Preço = (70 × m³ + 10 × m²) × 100/60
        preco_pavimento_custo = 70 * laje_m3 + 10 * laje_m2
        # Converter de preço de custo para preço de venda (× 100/60)
        preco_pavimento_venda = preco_pavimento_custo * 100 / 60
        
        construcao_laje['pavimento_terreo'] = {
            'name': f'Fornecimento e execução do pavimento térreo com {laje_espessura_cm}cm de espessura, através de enchimento e espalhamento de brita com diâmetro de 12mm a 20mm, colocação de camada de compressão em betão e todos os trabalhos e materiais para o seu perfeito acabamento.',
            'price': round(preco_pavimento_venda, 2),
            'quantity': 1,
            'unit': 'un',
            'item_type': 'incluido',
            'reasoning': f'Laje de {laje_m2:.2f}m² × {laje_espessura_cm}cm: (70 × {laje_m3:.3f} + 10 × {laje_m2:.2f}) × 100/60',
            'can_change_type': True
        }
        
        # Item 2: Revestimento (se aplicável)
        revestimento_laje = answers.get('revestimento_laje', 'nao')
        if revestimento_laje == 'sim':
            material_escolhido = answers.get('material_revestimento', '')
            
            if material_escolhido and material_escolhido in precos_revestimento:
                preco_material = precos_revestimento[material_escolhido]
                nome_material = nomes_materiais[material_escolhido]
                tipo_material = tipos_materiais[material_escolhido]
                
                # Preço = (15 + 13 + preço_material) × m² × 100/60
                preco_revestimento_custo = (15 + 13 + preco_material) * laje_m2
                preco_revestimento_venda = preco_revestimento_custo * 100 / 60
                
                # Ajustar nome do produto baseado no tipo
                if tipo_material == 'ceramico':
                    nome_produto = f'Revestimento da laje em cerâmica - {nome_material}'
                else:
                    nome_produto = f'Revestimento da laje em pedra natural - {nome_material}'
                
                construcao_laje['revestimento_laje'] = {
                    'name': nome_produto,
                    'price': round(preco_revestimento_venda, 2),
                    'quantity': 1,
                    'unit': 'un',
                    'item_type': 'incluido',
                    'reasoning': f'Revestimento {laje_m2:.2f}m² com {nome_material}: (15 + 13 + {preco_material}) × {laje_m2:.2f} × 100/60',
                    'can_change_type': True,
                    'material_type': tipo_material,
                    'material_price_per_m2': preco_material
                }
        
        return construcao_laje
