@echo off
echo ===============================================
echo   CONSTRUINDO EXECUTAVEL - SISTEMA PISCINAS
echo ===============================================

echo.
echo Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo.
echo Construindo executavel...
pyinstaller --clean app.spec

echo.
if exist "dist\Orcamentacao_Piscinas.exe" (
    echo ✅ SUCESSO! Executavel criado em: dist\Orcamentacao_Piscinas.exe
    echo.
    echo Para testar, execute: dist\Orcamentacao_Piscinas.exe
    echo.
) else (
    echo ❌ ERRO! Falha ao criar executavel.
    echo Verifique os logs acima para detalhes.
)

echo.
pause
