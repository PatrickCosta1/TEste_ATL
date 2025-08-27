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
## MAC:
# instalar Xcode Command Line Tools (necessário para compilar extensões)
xcode-select --install
# instalar Homebrew (se quiser gerir pacotes)
# cole o comando que aparece em https://brew.sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# instala python3 e pip3
brew install python   
python3 --version

cd /caminho/para/SeuProjeto
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

pip install -r requirements.txt
pip install pyinstaller

# exemplo usando wsgi.py como entrypoint
pyinstaller --clean --onefile \
  --name "OrcamentoPiscinas" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --add-data "database:database" \
  wsgi.py


SE BLOQUEAR::
  cd dist
chmod +x OrcamentoPiscinas
# remover quarentena (se mac bloquear)
xattr -d com.apple.quarantine OrcamentoPiscinas 2>/dev/null || true
./OrcamentoPiscinas
# ver arquitetura
file OrcamentoPiscinas

## 📁 **Ficheiros Essenciais**
- `app.py` - Aplicação principal
- `templates/` - Interface HTML
- `static/` - CSS, JS, imagens  
- `database/` - Banco de dados
- `dist/` - Executável final
- `build_exe.bat` - Gerar executável
