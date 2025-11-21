"""
Archivo: helpers.py
Ubicación: src/cogs/events_wizard/utils/

Descripción:
Utilidades internas específicas del Events Wizard.

Incluye:
- TOTAL_STEPS: número total de pasos del Events Wizard.
- event_step_header(): genera un encabezado dinámico estándar
  para cada paso del asistente, con numeración coherente.

Este módulo es exclusivo del Events Wizard y no se utiliza fuera de él.
"""

# --------------------------------------------------------
# 🔢 PASOS DEL WIZARD DE EVENTOS
# --------------------------------------------------------

# Número total de pasos definidos en el flujo actual:
# 1. Título
# 2. Tipo de evento
# 3. Circuito
# 4. Vehículos
# 5. Configuración técnica
# 6. Reglas / briefing / skins
# 7. Finalizar / publicar
TOTAL_STEPS = 7


# --------------------------------------------------------
# 🧩 ENCABEZADO DINÁMICO
# --------------------------------------------------------

def event_step_header(step_number: int, title: str) -> str:
    """
    Genera un encabezado estandarizado para un paso del Events Wizard.

    Args:
        step_number (int): número del paso actual.
        title (str): título descriptivo del paso.

    Returns:
        str: Ejemplo → "🧩 Paso 3/7 — Selección de circuito"
    """
    return f"🧩 **Paso {step_number}/{TOTAL_STEPS} — {title}**"
