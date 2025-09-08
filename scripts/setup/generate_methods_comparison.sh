#!/bin/bash
echo "========================================"
echo " 📊 METHODS COMPARISON REPORT GENERATOR"
echo " 4 Data Collection Methods Analysis"
echo "========================================"
echo

# Change to project root
cd "$(dirname "$0")/../.."

echo "[INFO] Generating HTML comparison report..."
python3 scripts/reports/methods_comparison_report.py

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to generate report"
    exit 1
fi

echo
echo "[OK] Report generated successfully!"
echo "[INFO] File saved in: output/Comparativo_Completo_Metodos_Coleta_Dados.html"
echo
echo "[INFO] To convert to PDF:"
echo "  - Open HTML in browser"
echo "  - Use Ctrl+P > Save as PDF"

echo
read -p "Open output folder? (y/n): " open_choice
if [[ "$open_choice" =~ ^[Yy]$ ]]; then
    if command -v xdg-open > /dev/null; then
        xdg-open output
    elif command -v open > /dev/null; then
        open output
    else
        echo "[INFO] Please manually open the output folder"
    fi
fi