import math

class PoolCalculator:
    """Calculadora de métricas da piscina baseada nas fórmulas fornecidas"""
    
    def __init__(self):
        # Factor de inflação 2025 - REDUZIDO AINDA MAIS
        # Balanceado considerando que produtos premium são adicionados via respostas
        self.FACTOR_INFLACAO_2024 = 1.04  # +4% (era 1.06) - Ainda mais moderado
    
    def calculate_all_metrics(self, comprimento, largura, prof_min, prof_max):
        """
        Calcula todas as métricas da piscina baseado nas dimensões
        
        Args:
            comprimento (float): C3 - Comprimento da piscina
            largura (float): D3 - Largura da piscina  
            prof_min (float): E3 - Profundidade mínima
            prof_max (float): F3 - Profundidade máxima
            
        Returns:
            dict: Dicionário com todas as métricas calculadas
        """
        
        # Cálculos baseados nas fórmulas fornecidas
        results = {}
        
        # G3 = (E3+F3)/2 - Profundidade média
        prof_media = (prof_min + prof_max) / 2
        results['prof_media'] = round(prof_media, 2)
        
        # H3 = (C3*D3*G3) - Volume
        volume = comprimento * largura * prof_media
        results['volume'] = round(volume, 2)
        
        # I3 = (C3*D3*G3)/4 - m3/h
        m3_h = volume / 4
        results['m3_h'] = round(m3_h, 2)
        
        # C5 = ((C3+0.4)*(D3+0.4))*0.15 + m2paredes*0.16 - m3 massa (atualizado conforme pedido)
        # Nota: E5 (m2_paredes) será calculado primeiro
        m2_paredes = (comprimento * 2 + largura * 2) * prof_media
        m3_massa = (((comprimento + 0.4) * (largura + 0.4)) * 0.15) + (m2_paredes * 0.16)
        results['m3_massa'] = round(m3_massa, 2)
        
        # D5 = (C3+0.4)*(D3+0.4) - m2 fundo (atualizado conforme pedido)
        m2_fundo = (comprimento + 0.4) * (largura + 0.4)
        results['m2_fundo'] = round(m2_fundo, 2)
        
        # E5 = +(C3*2+D3*2)*G3 - m2 paredes
        results['m2_paredes'] = round(m2_paredes, 2)
        
        # F5 = +(SE(F3<1,65;C3*2+D3*2;"erro")+C3/1,6*D3)*1,65 - m2(tela)
        if prof_max < 1.65:
            m2_tela = (comprimento * 2 + largura * 2 + comprimento / 1.6 * largura) * 1.65
        else:
            m2_tela = 0  # erro - implementar tratamento adequado
            results['erro_tela'] = "Profundidade máxima >= 1,65m"
            
        results['m2_tela'] = round(m2_tela, 2) if m2_tela > 0 else 0
        
        # G5 = ((C3+C3+D3+D3+(0,5*4))) - ml da bordadura
        ml_bordadura = comprimento + comprimento + largura + largura + (0.5 * 4)
        results['ml_bordadura'] = round(ml_bordadura, 2)
        
        # Perímetro da piscina (necessário para cálculo do heliaço)
        perimetro = (comprimento + largura) * 2
        results['perimetro'] = round(perimetro, 2)
        
        # H5 = INT((F5/(42))+1) - Rolos TL
        rolos_tl = math.floor((m2_tela / 42) + 1) if m2_tela > 0 else 0
        results['rolos_tl'] = rolos_tl
        
        # I5 = INT((F5/33))+1 - Rolos 3D
        rolos_3d = math.floor((m2_tela / 33) + 1) if m2_tela > 0 else 0
        results['rolos_3d'] = rolos_3d
        
        return results
    
    def calculate_complexity_multiplier(self, answers, dimensions):
        """
        Calcular multiplicador de complexidade baseado em metodologia da indústria.
        Baseado em estudos de custos de construção de piscinas e fatores de complexidade real.
        
        Metodologia:
        - Fatores geométricos (forma, dimensões)
        - Fatores técnicos e tecnológicos
        - Fatores de localização e infraestrutura
        - Factor de mercado e inflação
        
        NOTA: Factor de acesso foi removido e substituído por custos específicos de transporte de areia.
        
        Fórmula: Multiplicador = Base × Geo × Tech × Location × Market
        """
        
        # 1. FACTOR GEOMÉTRICO (1.0 - 1.35)
        # Baseado na complexidade da forma e proporções
        geo_factor = 1.0
        
        # Complexidade da forma
        forma = answers.get('forma', 'standard')
        if forma == 'especial':
            geo_factor *= 1.15  # Formas especiais requerem mais trabalho
        
        # Tipo de piscina (afeta estrutura e acabamentos)
        tipo = answers.get('tipo_piscina', 'skimmer')
        tipo_multipliers = {
            'skimmer': 1.0,         # Standard
            'espelho_dagua': 1.08,  # Requer acabamentos especiais
            'transbordo': 1.20      # Mais complexo estruturalmente
        }
        geo_factor *= tipo_multipliers.get(tipo, 1.0)
        
        # Factor de proporção (piscinas muito pequenas ou grandes são mais complexas por m²)
        area = dimensions.get('comprimento', 0) * dimensions.get('largura', 0)
        if area < 15:  # Piscinas muito pequenas
            geo_factor *= 1.08
        elif area > 60:  # Piscinas muito grandes
            geo_factor *= 1.05
        
        # 2. FACTOR DE ACESSO REMOVIDO - Substituído por custos específicos de transporte
        # Os custos de acesso difícil são agora calculados separadamente na função calculate_transport_costs()
        
        # 3. FACTOR TÉCNICO E TECNOLÓGICO (1.0 - 1.12) - REDUZIDO
        tech_factor = 1.0
        
        # Domótica/Automação - REDUZIDO
        if answers.get('domotica') == 'true':
            tech_factor *= 1.04  # Reduzido ainda mais (era 1.06) - produtos já incluídos
        
        # Tipo de revestimento
        revestimento = answers.get('revestimento', 'tela')
        if revestimento == 'ceramica':
            tech_factor *= 1.05  # Reduzido ainda mais (era 1.08) - cerâmicas já custam mais
        
        # Tipo de alimentação elétrica
        if answers.get('luz') == 'trifasica':
            tech_factor *= 1.03  # Instalação elétrica mais complexa
        
        # Escavação afeta trabalho técnico
        if answers.get('escavacao') == 'true':
            tech_factor *= 1.02  # +2% - reduzido ainda mais (era 1.03)
        
        # REMOVIDO: FACTOR DE LOCALIZAÇÃO - Não faz sentido económico
        # Interior vs exterior não justifica multiplicador significativo
        
        # 4. FACTOR DE MERCADO 2025 (1.05) - REDUZIDO AINDA MAIS
        # Mais equilibrado considerando que produtos premium são adicionados via respostas
        market_factor = 1.05  # Reduzido (era 1.08) - mais competitivo
        
        # CÁLCULO FINAL (sem factor de localização e acesso)
        final_multiplier = geo_factor * tech_factor * market_factor
        
        # Limitação de segurança (não exceder 125% do custo base) - REDUZIDO
        # Considerando que custos de acesso são agora específicos
        final_multiplier = min(final_multiplier, 1.25)  # Reduzido ainda mais (era 1.40)
        
        # Dados para transparência (3 fatores principais)
        breakdown = {
            'geometrico': round(geo_factor, 3),
            'tecnologico': round(tech_factor, 3),
            'mercado': round(market_factor, 3),
            'final': round(final_multiplier, 3)
        }
        
        return final_multiplier, breakdown

    def calculate_transport_costs(self, answers, metrics):
        """
        Calcula custos específicos de transporte de areia baseado no nível de acesso.
        
        Nova lógica implementada em 2025:
        - Acesso DIFÍCIL: 10€ por m³ de areia + 500€ de transporte fixo
        - Acesso MÉDIO: 25% dos valores do acesso difícil (2.50€ por m³ + 125€ fixo)
        - Acesso FÁCIL: Sem custos adicionais
        
        Args:
            answers (dict): Respostas do questionário
            metrics (dict): Métricas calculadas da piscina
            
        Returns:
            dict: Custos de transporte detalhados
        """
        
        acesso = answers.get('acesso', 'facil')
        m3_massa = metrics.get('m3_massa', 0)
        
        # Inicializar custos
        transport_costs = {
            'nivel_acesso': acesso,
            'custo_por_m3': 0.0,
            'custo_transporte_fixo': 0.0,
            'custo_total_m3': 0.0,
            'custo_total': 0.0,
            'm3_massa_usado': m3_massa,
            'explicacao': '',
            'breakdown': []
        }
        
        if acesso == 'dificil':
            # Acesso difícil: 10€ por m³ + 500€ fixo
            transport_costs['custo_por_m3'] = 10.0
            transport_costs['custo_transporte_fixo'] = 500.0
            transport_costs['explicacao'] = 'Acesso difícil ao local da obra'
            
        elif acesso == 'medio':
            # Acesso médio: 25% dos valores do acesso difícil
            transport_costs['custo_por_m3'] = 2.5  # 25% de 10€
            transport_costs['custo_transporte_fixo'] = 125.0  # 25% de 500€
            transport_costs['explicacao'] = 'Acesso médio ao local da obra (25% do custo de acesso difícil)'
            
        else:  # facil
            # Acesso fácil: sem custos adicionais
            transport_costs['explicacao'] = 'Acesso fácil - sem custos adicionais de transporte'
            
        # Calcular custos totais
        if m3_massa > 0:
            transport_costs['custo_total_m3'] = round(m3_massa * transport_costs['custo_por_m3'], 2)
        
        transport_costs['custo_total'] = round(
            transport_costs['custo_total_m3'] + transport_costs['custo_transporte_fixo'], 2
        )
        
        # Breakdown detalhado para transparência
        if transport_costs['custo_total'] > 0:
            transport_costs['breakdown'] = [
                {
                    'descricao': f'Custo por m³ de massa ({m3_massa:.2f} m³)',
                    'calculo': f'{m3_massa:.2f} × {transport_costs["custo_por_m3"]:.2f}€',
                    'valor': transport_costs['custo_total_m3']
                },
                {
                    'descricao': 'Custo fixo de transporte',
                    'calculo': f'{transport_costs["custo_transporte_fixo"]:.2f}€',
                    'valor': transport_costs['custo_transporte_fixo']
                }
            ]
        
        return transport_costs

    def get_multiplier_acesso(self, nivel_acesso):
        """Retorna multiplicador baseado no nível de acesso - REDUZIDO 2025"""
        multipliers = {
            'facil': 1.00,    # Acesso directo, sem complicações
            'medio': 1.06,    # +6% - reduzido (era 1.08)
            'dificil': 1.15   # +15% - reduzido (era 1.18)
        }
        return multipliers.get(nivel_acesso.lower(), 1.00)
    
    def get_multiplier_escavacao(self, tem_escavacao):
        """Retorna multiplicador se há escavação - REDUZIDO 2025"""
        return 1.03 if tem_escavacao else 1.00  # Reduzido (era 1.08)
    
    def get_multiplier_forma(self, forma):
        """Retorna multiplicador baseado na forma - AJUSTADO 2025"""
        # Moldes customizados mais caros devido escassez mão-obra especializada
        multipliers = {
            'standard': 1.00,  # Formas rectangulares/ovais standard
            'especial': 1.15   # +15% - moldes customizados (era 1.12)
        }
        return multipliers.get(forma.lower(), 1.00)
    
    def get_multiplier_domotica(self, tem_domotica):
        """Retorna multiplicador para integração domótica - REDUZIDO 2025"""
        # Produtos domóticos específicos já são adicionados ao orçamento
        return 1.06 if tem_domotica else 1.00  # Reduzido (era 1.08)
    
    def calculate_final_multiplier(self, answers, dimensions=None):
        """Usar o novo sistema de multiplicador de complexidade"""
        if dimensions is None:
            dimensions = {'comprimento': 8, 'largura': 4}  # Default
        
        multiplier, breakdown = self.calculate_complexity_multiplier(answers, dimensions)
        return multiplier
    
    def get_multiplier_breakdown(self, answers, dimensions=None):
        """Retorna breakdown detalhado dos multiplicadores para transparência"""
        if dimensions is None:
            dimensions = {'comprimento': 8, 'largura': 4}  # Default
            
        multiplier, breakdown = self.calculate_complexity_multiplier(answers, dimensions)
        return breakdown
