"""
Módulo: scheduler_wizard
Ubicación: src/cogs/scheduler_wizard/

Descripción general:
Este módulo implementa el asistente de programación de eventos (Scheduler Wizard),
el cual permite definir cuándo y cómo se publicarán los eventos creados mediante
el Events Wizard.

Funcionalidades clave:
1. Asignar una fecha/hora de publicación (programación automática).
2. Configurar la apertura de inscripciones (inmediata o personalizada).
3. Establecer recordatorios automáticos para pilotos o administradores.
4. Confirmar la programación final y registrar el evento con estado `scheduled`.

Estructura interna:
- `handlers/` → Controla el flujo general del asistente.
- `steps/` → Contiene los pasos interactivos (nombre, publicación, recordatorios, etc.).
- `views/` → Define componentes visuales reutilizables (botones, menús, modales).

Notas:
El asistente está diseñado para interoperar directamente con `events_wizard`,
recibiendo los datos del evento actual mediante la sesión activa (`EventWizardSession`),
y transfiriendo el resultado final a la base de datos con `status='scheduled'`.
"""
