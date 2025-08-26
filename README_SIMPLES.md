# Sistema de Orçamentação de Piscinas

Sistema completo para criação de orçamentos de piscinas com interface web moderna.

## 🚀 **Como Usar**

### Executável (Recomendado)
1. Execute: `dist\Orcamentacao_Piscinas.exe` 
2. Aguarde o navegador abrir automaticamente

### Desenvolvimento
```bash
python app.py
```

## 🔄 **Atualizar Executável**
Após modificar o código:
```bash
python -m PyInstaller --onefile --console --add-data "static;static" --add-data "templates;templates" --add-data "database/pool_budgets.db;." --name "OrcamentoPiscinas" run_app.py --clean
```

## 📁 **Ficheiros Essenciais**
- `app.py` - Aplicação principal
- `templates/` - Interface HTML
- `static/` - CSS, JS, imagens  
- `database/` - Banco de dados
- `dist/` - Executável final
- `build_exe.bat` - Gerar executável
