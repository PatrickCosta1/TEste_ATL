@echo off
echo ===============================================
echo   ATUALIZANDO EXECUTAVEL - SISTEMA PISCINAS
echo ===============================================

echo.
echo [1/4] Testando aplicacao em modo desenvolvimento...
echo Pressione Ctrl+C para parar quando confirmar que funciona
echo.
timeout /t 3 /nobreak >nul
start /wait python app.py

echo.
echo [2/4] Limpando build anterior...
if exist "build" rmdir /s /q "build"
if exist "dist\Orcamentacao_Piscinas.exe" del "dist\Orcamentacao_Piscinas.exe"

echo.
echo [3/4] Construindo novo executavel...
python -m PyInstaller --clean app.spec

echo.
echo [4/4] Verificando resultado...
if exist "dist\Orcamentacao_Piscinas.exe" (
    echo ✅ SUCESSO! Executavel atualizado!
    echo.
    echo 📁 Local: dist\Orcamentacao_Piscinas.exe
    echo 📊 Tamanho:
    dir "dist\Orcamentacao_Piscinas.exe" | find "Orcamentacao_Piscinas.exe"
    echo.
    set /p testar="Deseja testar o executavel agora? (s/n): "
    if /i "%testar%"=="s" (
        echo Iniciando executavel...
        start "" "dist\Orcamentacao_Piscinas.exe"
    )
) else (
    echo ❌ ERRO! Falha ao criar executavel.
    echo Verifique os logs acima para detalhes.
)

echo.
pause
