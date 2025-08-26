#!/bin/bash

echo "====================================="
echo "  Construindo Executável do Sistema"
echo "  de Orçamentação de Piscinas"
echo "====================================="
echo

echo "Limpando arquivos anteriores..."
rm -rf dist build

echo
echo "Construindo executável..."
pyinstaller main.spec --clean

echo
if [ -f "dist/OrcamentoPiscinas/OrcamentoPiscinas" ]; then
    echo "====================================="
    echo "  SUCESSO! Executável criado em:"
    echo "  dist/OrcamentoPiscinas/"
    echo "====================================="
    echo
    echo "Para usar:"
    echo "1. Vá para a pasta dist/OrcamentoPiscinas/"
    echo "2. Execute ./OrcamentoPiscinas"
    echo
else
    echo "====================================="
    echo "  ERRO na criação do executável!"
    echo "====================================="
fi

read -p "Pressione Enter para continuar..."
