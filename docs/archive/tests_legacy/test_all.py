import os
import sys
import pytest

# Asegurar que src esté en el path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    print("🧪 Iniciando test suite completa de Community Race Manager...\n")

    # Ejecución de pytest con cobertura y reporte resumido
    exit_code = pytest.main([
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
        "-s",
        "src/tests"
    ])

    print("\n📊 Informe HTML generado en: coverage_html_report/index.html")
    print("✅ Tests completados. Revisa la salida arriba para más detalles.")
    sys.exit(exit_code)
