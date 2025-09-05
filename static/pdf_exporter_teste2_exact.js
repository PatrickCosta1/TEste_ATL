/**
 * Sistema de Exportação PDF - EXATAMENTE IGUAL AO TESTE2
 * Baseado no script.js original do teste2
 * Coordenadas e funcionalidades idênticas
 */

// Função para remover apenas emojis que causam erro WinAnsi
function sanitizeText(text) {
  if (!text) return '';
  // Remove apenas emojis (faixa U+1F000-U+1F9FF)
  return text.replace(/[\u{1F000}-\u{1F9FF}]/gu, '[?]');
}

// Função principal para gerar PDF (igual ao teste2)
async function gerarPDF(orcamento) {
  try {
    // Caminho do modelo PDF (igual ao teste2)
    const modeloUrl = window.location.origin + '/static/template_orcamento.pdf';
    
    // Carregar PDF modelo
    const modeloBytes = await fetch(modeloUrl).then(r => r.arrayBuffer());
    const { PDFDocument, StandardFonts, rgb } = window.PDFLib;
    const pdfDoc = await PDFDocument.load(modeloBytes);
    
    // Fonte para textos dinâmicos
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
    
    // Preencher informações na segunda página (dados do cliente e piscina)
    const paginaInfo = pdfDoc.getPage(1); // 0 = capa, 1 = info
    
    // Coordenadas ajustadas conforme o modelo em branco (EXATAS DO TESTE2)
    // Cabeçalho - com validação para evitar valores undefined
    paginaInfo.drawText(sanitizeText(orcamento.proposta) || '', { x: 133, y: 625, size: 13, font: fontBold, color: rgb(0, 0.059, 0.329) }); // Nº Proposta
    paginaInfo.drawText(sanitizeText(orcamento.comercial) || '', { x: 133, y: 577, size: 13, font: fontBold, color: rgb(0, 0.059, 0.329) }); // Comercial (negrito)
    paginaInfo.drawText(sanitizeText(orcamento.cliente) || '', { x: 458, y: 625, size: 13, font: fontBold, color: rgb(0, 0.059, 0.329) }); // A/C Sr(a).
  // Mostrar localidade: se for 'Outro' usar localidade_outro quando disponível
  const localidadeParaPDF = (orcamento.localidade === 'Outro' && orcamento.localidade_outro) ? orcamento.localidade_outro : (orcamento.localidade || '');
  paginaInfo.drawText(sanitizeText(localidadeParaPDF) || '', { x: 458, y: 577, size: 13, font: fontBold, color: rgb(0, 0.059, 0.329) }); // Localidade
    paginaInfo.drawText(`${new Date().toLocaleDateString()}`, { x: 458, y: 528, size: 13, font: fontBold, color: rgb(0, 0.059, 0.329) }); // Data
    
    // Detalhes da Piscina (COORDENADAS EXATAS DO TESTE2) - com validação
    paginaInfo.drawText(`${orcamento.piscina.comprimento || '0'}m`, { x: 176, y: 463.5, size: 12, font: font, color: rgb(0, 0.059, 0.329) }); // Comprimento
    paginaInfo.drawText(`${orcamento.piscina.largura || '0'}m`, { x: 143, y: 449, size: 12, font: font, color: rgb(0, 0.059, 0.329) }); // Largura
    paginaInfo.drawText(`${orcamento.piscina.profundidade || '0'}m`, { x: 176, y: 435, size: 12, font: font, color: rgb(0, 0.059, 0.329) }); // Profundidade
    
    if (orcamento.piscina.detalhes) {
      // Quebra de linha automática para texto longo (IGUAL AO TESTE2)
      const detalhes = sanitizeText(`${orcamento.piscina.detalhes}`);
      const maxWidth = 320; // largura máxima em pontos
      const x = 192;
      let y = 422;
      const lineHeight = 13;
      
      // Função para dividir texto em linhas que caibam na largura (IGUAL AO TESTE2)
      function splitText(text, font, size, maxWidth) {
        const words = text.split(' ');
        let lines = [];
        let currentLine = '';
        
        for (let word of words) {
          let testLine = currentLine ? currentLine + ' ' + word : word;
          let testWidth = font.widthOfTextAtSize(testLine, size);
          
          if (testWidth > maxWidth && currentLine) {
            lines.push(currentLine);
            currentLine = word;
          } else {
            currentLine = testLine;
          }
        }
        
        if (currentLine) lines.push(currentLine);
        return lines;
      } 
      
      const linhas = splitText(detalhes, font, 11, maxWidth);
      linhas.forEach(linha => {
        paginaInfo.drawText(sanitizeText(linha), { x, y, size: 11, font: font, color: rgb(0, 0.059, 0.329) });
        y -= lineHeight;
      });
    }
    
    // --- Adicionar página de produtos detalhados após a segunda página (IGUAL AO TESTE2) ---
    let produtos = orcamento.itens;
    if (produtos.length > 0) {
      // Agrupar produtos por categoria com organização hierárquica
      const categorias = {};
      produtos.forEach(item => {
        if (!categorias[item.categoria]) {
          categorias[item.categoria] = { incluidos: [], alternativos: [], opcionais: [] };
        }
        if (item.isAlternative) {
          categorias[item.categoria].alternativos.push(item);
        } else if (item.isOptional) {
          categorias[item.categoria].opcionais.push(item);
        } else {
          categorias[item.categoria].incluidos.push(item);
        }
      });

      // Organizar produtos com alternativos agrupados após seus principais
      const categoriasOrganizadas = {};
      Object.keys(categorias).forEach(categoria => {
        const organized = [];
        
        // Adicionar produtos incluídos com seus alternativos
        categorias[categoria].incluidos.forEach(incluido => {
          organized.push(incluido);
          // Adicionar alternativos relacionados a este produto
          categorias[categoria].alternativos.forEach(alternativo => {
            if (alternativo.alternative_to === incluido.productId) {
              organized.push(alternativo);
            }
          });
        });
        
        // Adicionar alternativos órfãos (sem relação)
        categorias[categoria].alternativos.forEach(alternativo => {
          if (!alternativo.alternative_to || !categorias[categoria].incluidos.some(inc => inc.productId === alternativo.alternative_to)) {
            organized.push(alternativo);
          }
        });
        
        // Adicionar opcionais por último
        organized.push(...categorias[categoria].opcionais);
        
        categoriasOrganizadas[categoria] = organized;
      });
      
  let currentPage = pdfDoc.insertPage(2, [595, 842]);
  // insertionIndex indica a posição onde serão inseridas as próximas páginas
  // para garantir que as páginas do template permaneçam no final do documento.
  let insertionIndex = 3;
  let y = 780;
      
      // Título (IGUAL AO TESTE2)
      currentPage.drawText('Orçamento', {
        x: 50, y, size: 15, font: fontBold, color: rgb(0.07, 0.22, 0.45)
      });
      y -= 32;
      
      // Cabeçalho da tabela (POSIÇÕES IGUAIS AO TESTE2)
      const colX = {
        produto: 70,
        qtd: 320,
        unidade: 360,
        preco: 410,
        subtotal: 490
      };
      const headerSize = 10;
      
      // Função para quebra de texto (IGUAL AO TESTE2)
      function splitText(text, font, size, maxWidth) {
        const words = text.split(' ');
        let lines = [];
        let currentLine = '';
        
        for (let word of words) {
          let testLine = currentLine ? currentLine + ' ' + word : word;
          let testWidth = font.widthOfTextAtSize(testLine, size);
          
          if (testWidth > maxWidth && currentLine) {
            lines.push(currentLine);
            currentLine = word;
          } else {
            currentLine = testLine;
          }
        }
        
        if (currentLine) lines.push(currentLine);
        return lines;
      }
      
      let totalGeral = 0;
      
      // Map de nomes de famílias para exibição no PDF (garante nomes estilizados)
      const familyDisplayNames = {
        'filtracao': 'Filtração',
        'recirculacao_iluminacao': 'Recirculação e Iluminação',
        'tratamento_agua': 'Tratamento de Água',
        'revestimento': 'Revestimento',
        'aquecimento': 'Aquecimento'
        // adicionar outras famílias se necessário
      };

      // Ordem desejada das famílias no PDF (preserva sequência definida no app)
      const familyOrder = ['filtracao', 'recirculacao_iluminacao', 'tratamento_agua', 'revestimento', 'aquecimento'];

      // Helper: normaliza uma string para chave comparável (remove acentos, caixa e espaços)
      function normalizeKey(s) {
        if (!s) return '';
        return s.toString().toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .replace(/[^a-z0-9]+/g, '_')
          .replace(/^_+|_+$/g, '');
      }

      // Criar um mapa das categories existentes com sua chave normalizada
      const categoriesMap = {}; // normalizedKey -> originalKey
      Object.keys(categoriasOrganizadas).forEach(origKey => {
        const nk = normalizeKey(origKey);
        categoriesMap[nk] = origKey;
      });

      // Construir orderedCategories usando familyOrder normalizada; aceitar também chaves originais
      const orderedCategories = [];
      familyOrder.forEach(fam => {
        const nk = normalizeKey(fam);
        if (categoriesMap[nk] && orderedCategories.indexOf(categoriesMap[nk]) === -1) {
          orderedCategories.push(categoriesMap[nk]);
        }
      });
      // Adicionar categorias restantes que não existem na familyOrder (mantendo ordem original)
      Object.keys(categoriasOrganizadas).forEach(origKey => {
        if (orderedCategories.indexOf(origKey) === -1) orderedCategories.push(origKey);
      });

      for (const categoria of orderedCategories) {
        console.log(`DEBUG: Renderizando categoria ${categoria} com ${categoriasOrganizadas[categoria].length} itens`);
        // Categoria título (estilizado com design premium) - IGUAL AO TESTE2
        if (y < 120) {
          currentPage = pdfDoc.insertPage(insertionIndex, [595, 842]);
          insertionIndex++;
          y = 780;
        }
        
        // Sombra sutil para o cabeçalho da categoria
        currentPage.drawRectangle({
          x: 52, y: y-4, width: 500, height: 20, color: rgb(0.85, 0.85, 0.85), opacity: 0.5
        });
        
        // Fundo principal da categoria com gradiente visual
        currentPage.drawRectangle({
          x: 50, y: y-2, width: 500, height: 20, 
          color: rgb(0.07, 0.22, 0.45),
          borderWidth: 1,
          borderColor: rgb(0.05, 0.15, 0.35)
        });
        
        // Determinar displayName: procurar por familyDisplayNames usando chave normalizada
        const normalizedCategoria = normalizeKey(categoria);
        const displayName = familyDisplayNames[normalizedCategoria] || familyDisplayNames[categoria] || categoria;
        currentPage.drawText(sanitizeText(displayName), {
          x: 60, y: y+3, size: 11, font: fontBold, color: rgb(1,1,1)
        });
        y -= 28;
        
        // Cabeçalho da tabela premium (IGUAL AO TESTE2 - mesmas colunas)
        // Fundo elegante para cabeçalho
        currentPage.drawRectangle({
          x: 65, y: y-8, width: 485, height: 18,
          color: rgb(0.95, 0.97, 1), // Azul muito claro
          borderWidth: 1.2,
          borderColor: rgb(0.7, 0.7, 0.7)
        });
        
        // Separadores verticais sutis para melhor organização
        const separadores = [315, 355, 405, 485];
        separadores.forEach(x => {
          currentPage.drawLine({
            start: { x, y: y+8 },
            end: { x, y: y-8 },
            thickness: 0.8,
            color: rgb(0.8, 0.8, 0.8)
          });
        });
        
        currentPage.drawText('Descritivo', { x: colX.produto, y: y-2, size: headerSize, font: fontBold, color: rgb(0.07,0.22,0.45) });
        currentPage.drawText('Quant.', { x: colX.qtd, y: y-2, size: headerSize, font: fontBold, color: rgb(0.07,0.22,0.45) });
        currentPage.drawText('Unid.', { x: colX.unidade, y: y-2, size: headerSize, font: fontBold, color: rgb(0.07,0.22,0.45) });
        currentPage.drawText('Preço Unit.', { x: colX.preco, y: y-2, size: headerSize, font: fontBold, color: rgb(0.07,0.22,0.45) });
        currentPage.drawText('Sub Total', { x: colX.subtotal, y: y-2, size: headerSize, font: fontBold, color: rgb(0.07,0.22,0.45) });
        
        // Linha divisória mais robusta
        currentPage.drawLine({
          start: { x: 65, y: y-12 },
          end: { x: 550, y: y-12 },
          thickness: 1.5,
          color: rgb(0.07, 0.22, 0.45)
        });
        y -= 18;
        
        let subtotalCategoria = 0;
        let itemIndex = 0; // Para alternar cores de fundo
        
        for (const item of categoriasOrganizadas[categoria]) {
          console.log(`DEBUG: Renderizando item ${item.nome} - Tipo: ${item.tipo}, isAlternative: ${item.isAlternative}, isOptional: ${item.isOptional}`);
          
          // Quebra de linha para nome do produto - indentação com símbolo para alternativos
          let nomeIndentado = sanitizeText(item.nome);
          if (item.isAlternative) {
            nomeIndentado = `    • ${sanitizeText(item.nome)}`; // Bullet point e indentação para alternativos
          }
          
          const produtoLinhas = splitText(nomeIndentado, font, 9, 230);
          const rowHeight = Math.max(13, 13 * produtoLinhas.length);
          
          // Fundo alternado para melhor legibilidade
          const corFundo = itemIndex % 2 === 0 ? rgb(0.98, 0.98, 0.98) : rgb(1, 1, 1);
          
          // Fundo especial para alternativos e opcionais
          let fundoFinal = corFundo;
          let corBorda = rgb(0.9, 0.9, 0.9);
          // Alternativos e opcionais mantêm o mesmo fundo (sem cor especial de fundo)
          // apenas a cor da letra será diferente
          
          // Desenhar fundo da linha
          currentPage.drawRectangle({
            x: 65, y: y - rowHeight + 8, width: 485, height: rowHeight,
            color: fundoFinal,
            borderWidth: 0.3, // Mesma espessura para todos os tipos
            borderColor: corBorda
          });
          
          // Separadores verticais para cada linha
          const separadores = [315, 355, 405, 485];
          separadores.forEach(x => {
            currentPage.drawLine({
              start: { x, y: y+4 },
              end: { x, y: y - rowHeight + 4 },
              thickness: 0.3,
              color: rgb(0.85, 0.85, 0.85)
            });
          });
          
          // Preço unitário e subtotal - tratamento especial para alternativos e opcionais
          let precoUnit, subtotal;
          if (item.tipo === 'Alternativo') {
            precoUnit = `€${item.preco.toLocaleString('pt-PT', {minimumFractionDigits:2})}`;
            subtotal = 'Alternativo';
          } else if (item.tipo === 'Opcional') {
            precoUnit = `€${item.preco.toLocaleString('pt-PT', {minimumFractionDigits:2})}`;
            subtotal = 'Opcional';
          } else if (item.tipo === 'Oferta' || item.tipo === 'oferta') {
            precoUnit = item.preco !== undefined ? `€${item.preco.toLocaleString('pt-PT', {minimumFractionDigits:2})}` : '';
            subtotal = 'Oferta';
          } else {
            precoUnit = item.preco !== undefined ? `€${item.preco.toLocaleString('pt-PT', {minimumFractionDigits:2})}` : '';
            subtotal = `€${item.subtotal.toLocaleString('pt-PT', {minimumFractionDigits:2})}`;
          }
          
          // Acumula subtotal da categoria e total geral (apenas itens normais)
          if (item.tipo === 'Normal') subtotalCategoria += item.subtotal;
          // Oferta não acumula (já tratada visualmente)
          
          // Produto (quebrado em linhas) com cores diferentes para cada tipo
          let produtoY = y;
          produtoLinhas.forEach((linha, index) => {
            // Cores: Normal (azul escuro), Alternativo (roxo), Opcional (dourado)
            let cor, tamanhoFonte;
            if (item.isAlternative) {
              cor = rgb(0.49, 0.23, 0.93); // Roxo para alternativos
              tamanhoFonte = 8; // Fonte menor para alternativos
            } else if (item.isOptional) {
              cor = rgb(0.851, 0.467, 0.043); // Dourado para opcionais (#d97706)  
              tamanhoFonte = 8; // Fonte menor para opcionais
            } else {
              cor = rgb(0.1, 0.2, 0.4); // Azul escuro para incluídos
              tamanhoFonte = 9; // Fonte normal para incluídos
            }
            
            currentPage.drawText(sanitizeText(linha), { x: colX.produto, y: produtoY, size: tamanhoFonte, font: font, color: cor });
            produtoY -= 13;
          });
          
          // Quantidade, Unidade, Preço mantêm cor padrão para não confundir
          let tamanhoFonte = item.isAlternative || item.isOptional ? 8 : 9; // Fonte menor para alt/opt
          let corPadrao = rgb(0.1, 0.2, 0.4); // Cor padrão azul escuro para todas as colunas normais
          
          currentPage.drawText(String(item.qtd), { x: colX.qtd, y, size: tamanhoFonte, font, color: corPadrao });
          const unidadeText = (item.unidade || '').toString().toLowerCase();
          currentPage.drawText(sanitizeText(unidadeText), { x: colX.unidade, y, size: tamanhoFonte, font, color: corPadrao });
          currentPage.drawText(sanitizeText(precoUnit), { x: colX.preco, y, size: tamanhoFonte, font, color: corPadrao });
          
          // Subtotal - APENAS esta coluna tem cores especiais
          if (item.tipo === 'Alternativo') {
            currentPage.drawText(sanitizeText(subtotal), { x: colX.subtotal, y, size: 8, font: fontBold, color: rgb(0.49, 0.23, 0.93) }); // Roxo
          } else if (item.tipo === 'Opcional') {
            currentPage.drawText(subtotal, { x: colX.subtotal, y, size: 8, font: fontBold, color: rgb(0.851, 0.467, 0.043) }); // Dourado
          } else {
            currentPage.drawText(subtotal, { x: colX.subtotal, y, size: tamanhoFonte, font, color: corPadrao });
          }
          
          y -= rowHeight + 3; // Adiciona 3 pontos de espaçamento vertical entre itens
          itemIndex++; // Incrementar para alternar cores
          
          if (y < 90) {
            currentPage = pdfDoc.insertPage(insertionIndex, [595, 842]);
            insertionIndex++;
            y = 780;
            itemIndex = 0; // Reset do contador em nova página
          }
        }
        
        // Subtotal da categoria com design premium - IGUAL AO TESTE2
        if (y < 100) {
          currentPage = pdfDoc.insertPage(insertionIndex, [595, 842]);
          insertionIndex++;
          y = 780;
        }
        
        y -= 8;
        
        // Fundo elegante para subtotal
        currentPage.drawRectangle({
          x: 400, y: y-6, width: 150, height: 18,
          color: rgb(0.95, 0.97, 1),
          borderWidth: 1,
          borderColor: rgb(0.07, 0.22, 0.45)
        });
        
      
        
        currentPage.drawText('Subtotal', {
          x: colX.preco, y: y, size: 10, font: fontBold, color: rgb(0.07,0.22,0.45)
        });
        currentPage.drawText(`€${subtotalCategoria.toLocaleString('pt-PT', {minimumFractionDigits:2})}`, {
          x: colX.subtotal, y: y, size: 10, font: fontBold, color: rgb(0.07,0.22,0.45)
        });
        y -= 30;
        totalGeral += subtotalCategoria;
      }
      
      // Total geral da página - USA O TOTAL FINAL COM MULTIPLICADORES (IGUAL AO TESTE2)
      if (y < 120) { // Aumentei o espaço necessário para incluir explicação
        currentPage = pdfDoc.insertPage(insertionIndex, [595, 842]);
        insertionIndex++;
        y = 780;
      }
      
      // Explicação dos multiplicadores (para o cliente) - NOVA ADIÇÃO
      y -= 15;
      currentPage.drawText('Ajustes Técnicos e Comerciais:', {
        x: 50, y, size: 10, font: fontBold, color: rgb(0.07, 0.22, 0.45)
      });
      
      y -= 12;
      let explicacaoTexto = 'O valor apresentado inclui ajustes baseados na complexidade técnica do projeto, ';
      explicacaoTexto += 'condições de acesso, especificações técnicas solicitadas e fatores de mercado vigentes.';
      
      // Dividir texto em linhas para caber na largura
      const maxWidthExplicacao = 500;
      const palavras = explicacaoTexto.split(' ');
      let linhaAtual = '';
      let linhas = [];
      
      for (const palavra of palavras) {
        const linhaTeste = linhaAtual + (linhaAtual ? ' ' : '') + palavra;
        const larguraTeste = font.widthOfTextAtSize(linhaTeste, 9);
        
        if (larguraTeste <= maxWidthExplicacao) {
          linhaAtual = linhaTeste;
        } else {
          if (linhaAtual) linhas.push(linhaAtual);
          linhaAtual = palavra;
        }
      }
      if (linhaAtual) linhas.push(linhaAtual);
      
      // Desenhar as linhas da explicação
      for (const linha of linhas) {
        currentPage.drawText(linha, {
          x: 50, y, size: 9, font, color: rgb(0.3, 0.3, 0.3)
        });
        y -= 11;
      }
      
      y -= 10; // Espaço antes do total
      
      // Calcular valores com IVA (23% padrão)
      const ivaRate = 0.23;
      const subtotalSemIva = orcamento.total;
      const ivaAmount = subtotalSemIva * ivaRate;
      const totalComIva = subtotalSemIva + ivaAmount;
      
      // === SUBTOTAL (SEM IVA) ===
      // Fundo para subtotal
      currentPage.drawRectangle({
        x: 340, y: y-2, width: 210, height: 18, 
        color: rgb(0.95, 0.97, 1),
        borderWidth: 1,
        borderColor: rgb(0.7, 0.7, 0.7)
      });
      
      currentPage.drawText('Subtotal (s/ IVA):', {
        x: 350, y: y+2, size: 10, font: fontBold, color: rgb(0.07, 0.22, 0.45)
      });
      
      currentPage.drawText(`€${subtotalSemIva.toLocaleString('pt-PT', {minimumFractionDigits:2})}`, {
        x: 470, y: y+2, size: 10, font: fontBold, color: rgb(0.07, 0.22, 0.45)
      });
      y -= 22;
      
      // === IVA ===
      // Fundo para IVA (verde claro)
      currentPage.drawRectangle({
        x: 340, y: y-2, width: 210, height: 18, 
        color: rgb(0.93, 0.99, 0.95),
        borderWidth: 1,
        borderColor: rgb(0.059, 0.6, 0.4)
      });
      
      currentPage.drawText('IVA (23%):', {
        x: 350, y: y+2, size: 10, font: fontBold, color: rgb(0.059, 0.6, 0.4)
      });
      
      currentPage.drawText(`€${ivaAmount.toLocaleString('pt-PT', {minimumFractionDigits:2})}`, {
        x: 470, y: y+2, size: 10, font: fontBold, color: rgb(0.059, 0.6, 0.4)
      });
      y -= 22;
      
      // === TOTAL COM IVA ===
      // Sombra sutil para o total
      currentPage.drawRectangle({
        x: 342, y: y-4, width: 210, height: 22, color: rgb(0.85, 0.85, 0.85), opacity: 0.5
      });
      
      // Fundo principal do total com bordas arredondadas visuais
      currentPage.drawRectangle({
        x: 340, y: y-2, width: 210, height: 22, 
        color: rgb(0.07, 0.22, 0.45),
        borderWidth: 2,
        borderColor: rgb(0.05, 0.15, 0.35)
      });
      
      currentPage.drawText('Total (c/ IVA):', {
        x: 350, y: y+4, size: 12, font: fontBold, color: rgb(1,1,1)
      });
      
      currentPage.drawText(`€${totalComIva.toLocaleString('pt-PT', {minimumFractionDigits:2})}`, {
        x: 470, y: y+4, size: 12, font: fontBold, color: rgb(1,1,1)
      });
      y -= 30;
    }
    // --- Fim da página de produtos detalhados agrupados ---

    // Gerar e baixar PDF (NOME IGUAL AO TESTE2)
    const propostaNumero = orcamento.proposta.replace(/\s+/g, '').replace('PO', '');
    const pdfBytes = await pdfDoc.save();
    const blob = new Blob([pdfBytes], { type: 'application/pdf' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `PO_${propostaNumero}_ORC.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error('Erro ao gerar PDF:', error);
    throw error;
  }
}

/**
 * Função adaptada para nosso sistema Flask
 * Converte dados do Flask para formato do teste2 e gera PDF
 */
async function exportBudgetToPDFTeste2() {
  try {
    // Obter dados da sessão do Flask
    const response = await fetch('/get_session_data');
    const sessionData = await response.json();
    
    const clientData = sessionData.client_data;
    const budgetData = sessionData.current_budget;
    
    if (!clientData || !budgetData) {
      throw new Error('Dados incompletos para gerar PDF');
    }

    // Debug: verificar dados recebidos
    console.log('Client Data:', clientData);
    console.log('Budget Data:', budgetData);

    // Converter dados do Flask para formato do teste2
    const orcamentoTeste2 = {
      cliente: clientData.clientName || '',
  localidade: clientData.localidade || '',
  localidade_outro: clientData.localidade_outro || '',
      comercial: clientData.commercialName || '',  // Corrigido: campo correto do formulário
      proposta: clientData.proposalNumber || '',
      piscina: {
        comprimento: budgetData.pool_info.dimensions.comprimento,
        largura: budgetData.pool_info.dimensions.largura,
        profundidade: budgetData.pool_info.dimensions.prof_max,
        detalhes: clientData.observations || ''
      },
      itens: [],
      total: budgetData.total_price, // TOTAL FINAL COM MULTIPLICADORES JÁ APLICADOS
      data: new Date().toLocaleDateString()
    };

    // Mapeamento de nomes técnicos para nomes com formatação portuguesa adequada
    const familyDisplayNames = {
      'filtracao': 'Filtração',
      'limpeza': 'Limpeza',
      'quimica': 'Química',
      'acessorios': 'Acessórios',
      'iluminacao': 'Iluminação',
      'aquecimento': 'Aquecimento',
      'automacao': 'Automação'
    };

    // Normalizadores e utilitários para garantir que nomes de família sejam formatados corretamente
    function normalizeKey(s) {
      if (!s) return '';
      return s.toString()
        .normalize('NFD')                       // separar diacríticos
        .replace(/[\u0300-\u036f]/g, '')      // remover diacríticos
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '');            // remover espaços e caracteres não alfanuméricos
    }

    function toTitleCase(s) {
      if (!s) return '';
      return s.toString().replace(/[_\-]+/g, ' ').split(' ').map(part => {
        return part ? part.charAt(0).toUpperCase() + part.slice(1).toLowerCase() : '';
      }).join(' ');
    }

    // Construir um mapeamento normalizado para lookup rápido
    const normalizedFamilyDisplayNames = {};
    Object.entries(familyDisplayNames).forEach(([k, v]) => {
      normalizedFamilyDisplayNames[normalizeKey(k)] = v;
    });

    // Converter produtos do Flask para formato do teste2
    console.log('DEBUG: Processando budgetData.families:', Object.keys(budgetData.families));
    Object.entries(budgetData.families).forEach(([familyName, products]) => {
  const displayName = normalizedFamilyDisplayNames[normalizeKey(familyName)] || toTitleCase(familyName);
      console.log(`DEBUG: Família ${familyName} (${displayName}) com ${Object.keys(products).length} produtos`);
      
      // Primeiro processar produtos incluídos
      Object.entries(products).forEach(([productId, product]) => {
        console.log(`DEBUG: Produto ${product.name} - quantity: ${product.quantity}, item_type: ${product.item_type}`);
        if (product.quantity > 0 && (product.item_type === 'incluido' || product.was_optional)) {
          console.log('DEBUG: Adicionando produto INCLUÍDO:', product.name);
          // Remover sufixos do nome para o PDF
          const cleanName = product.name.replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '');
          orcamentoTeste2.itens.push({
            categoria: displayName,
            nome: cleanName,
            unidade: product.unit || 'un',
            preco: product.price,
            qtd: product.quantity,
            tipo: 'Normal',
            subtotal: product.price * product.quantity,
            isOptional: false,
            productId: productId
          });
        }
      });
      
      // Depois processar produtos alternativos
      Object.entries(products).forEach(([productId, product]) => {
        if (product.item_type === 'alternativo') {
          console.log('DEBUG: Adicionando produto ALTERNATIVO:', product.name);
          // Remover sufixos do nome para o PDF
          const cleanName = product.name.replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '');
          orcamentoTeste2.itens.push({
            categoria: displayName,
            nome: cleanName,
            unidade: product.unit || 'un',
            preco: product.price,
            qtd: product.quantity || 0,
            tipo: 'Alternativo',
            subtotal: 0, // Não conta no total
            isAlternative: true,
            productId: productId,
            alternative_to: product.alternative_to
          });
        }
      });
      
      // Por último processar produtos opcionais
      Object.entries(products).forEach(([productId, product]) => {
        if (product.item_type === 'opcional') {
          console.log('DEBUG: Adicionando produto OPCIONAL:', product.name);
          // Remover sufixos do nome para o PDF
          const cleanName = product.name.replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '');
          orcamentoTeste2.itens.push({
            categoria: displayName,
            nome: cleanName,
            unidade: product.unit || 'un',
            preco: product.price,
            qtd: product.quantity || 0,
            tipo: 'Opcional',
            subtotal: 0, // Não conta no total
            isOptional: true,
            productId: productId
          });
        }
      });
      
      // Processar produtos marcados como Oferta (não contam para o total, devem aparecer como 'Oferta' no PDF)
      Object.entries(products).forEach(([productId, product]) => {
        if (product.item_type === 'oferta' || product.item_type === 'Oferta') {
          console.log('DEBUG: Adicionando produto OFERTA:', product.name);
          const cleanName = (product.name || '').replace(' (ALTERNATIVO)', '').replace(' (OPCIONAL)', '').replace(' (OFERTA)', '');
          orcamentoTeste2.itens.push({
            categoria: displayName,
            nome: cleanName,
            unidade: product.unit || 'un',
            preco: product.price,
            qtd: product.quantity || 0,
            tipo: 'Oferta',
            subtotal: 0, // Não conta no total
            isOffer: true,
            productId: productId
          });
        }
      });
    });
    
    console.log('DEBUG: Total de itens processados:', orcamentoTeste2.itens.length);
    console.log('DEBUG: Itens opcionais encontrados:', orcamentoTeste2.itens.filter(item => item.isOptional).length);

    // Gerar PDF usando a função exata do teste2
    await gerarPDF(orcamentoTeste2);

  } catch (error) {
    console.error('Erro ao exportar PDF:', error);
    alert('Erro ao gerar PDF: ' + error.message);
  }
}

// Função global para ser chamada pelos botões
function exportBudgetToPDF() {
  exportBudgetToPDFTeste2();
}
