@echo off
echo A instalar dependencias...
pip install pyinstaller
echo A criar o executável...
pyinstaller --onefile --noconsole stock_monitor.pyw
echo.
echo Construção concluída! O executável está na pasta "dist". Podes fechar esta janela.
pause
 