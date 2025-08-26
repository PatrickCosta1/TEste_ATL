#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arquivo de entrada para o executável do Sistema de Orçamentação de Piscinas
"""

import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

# Adicionar o diretório do projeto ao path
if hasattr(sys, '_MEIPASS'):
    # Executável PyInstaller
    basedir = sys._MEIPASS
else:
    # Desenvolvimento
    basedir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, basedir)

# Importar a aplicação Flask
from app import app

def open_browser():
    """Abre o navegador após 1.5 segundos"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

def main():
    """Função principal"""
    print("=== SISTEMA DE ORÇAMENTAÇÃO DE PISCINAS ===")
    print("Iniciando servidor...")
    print("Aguarde, o navegador abrirá automaticamente...")
    
    # Abrir navegador em thread separada
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Executar Flask com debug temporário para diagnóstico
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        input("Pressione Enter para sair...")

if __name__ == '__main__':
    main()
