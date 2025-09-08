@echo off
echo ========================================
echo  📊 METHODS COMPARISON REPORT GENERATOR
echo  4 Data Collection Methods Analysis
echo ========================================
echo.

:: Change to project root
cd /d "%~dp0..\.."

echo [INFO] Generating HTML comparison report...
python scripts\reports\methods_comparison_report.py

if errorlevel 1 (
    echo [ERROR] Failed to generate report
    pause
    exit /b 1
)

echo.
echo [OK] Report generated successfully!
echo [INFO] File saved in: output\Comparativo_Completo_Metodos_Coleta_Dados.html
echo.
echo [INFO] To convert to PDF:
echo   - Open HTML in browser
echo   - Use Ctrl+P ^> Save as PDF

echo.
echo Open output folder? (Y/N)
set /p open_choice=
if /i "%open_choice%"=="Y" (
    start "" "output"
)

pause