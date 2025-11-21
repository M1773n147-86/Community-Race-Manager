# 🏁 Community Race Manager — Roadmap de desarrollo

## 🧩 Estado actual
✅ Bot funcional y conectado a Discord  
✅ Base de datos inicial operativa  
✅ Comandos slash principales cargados correctamente  
✅ Sistema de roles y permisos implementado  
✅ Wizard `/create_event` en desarrollo activo

---

## 🚧 Próximos pasos inmediatos

### 🎯 Fase 1 — Gestión avanzada de eventos
- [ ] Agregar campo `is_published` a la DB de eventos  
- [ ] Modificar wizard `/create_event` → botones "Publicar ahora" y "Guardar evento"  
- [ ] Crear comandos:
  - [ ] `/load_saved_event` — cargar eventos guardados  
  - [ ] `/edit_saved_event` — editar o duplicar configuraciones  
  - [ ] `/delete_event` — eliminar eventos guardados  
- [ ] Implementar comprobación previa: mostrar mensaje si no hay eventos guardados  

---

### 🗓️ Fase 2 — Gestión de campeonatos
- [ ] Permitir crear eventos agrupados bajo un campeonato  
- [ ] Crear sistema de rondas (rondas automáticas basadas en plantillas de eventos)  
- [ ] Generar calendario de publicaciones automáticas  

---

### 🌍 Fase 3 — Localización e idioma
- [ ] Implementar sistema multilenguaje (ES / EN / FR)  
- [ ] Crear archivos JSON en `src/locales/`  
- [ ] Agregar comando `/select_language`  
- [ ] Traducir texto de interfaz y mensajes  

---

### 🔄 Fase 4 — Importación y exportación
- [ ] `/import_event` — importar configuraciones externas  
- [ ] `/export_event` — exportar configuraciones  
- [ ] Verificar compatibilidad de estructura de datos  

---

### ⚙️ Fase 5 — Mejoras backend
- [ ] Persistencia de wizard ante reinicios  
- [ ] Sistema de tareas programadas (cronjobs) para recordatorios  
- [ ] Sistema anti-alt (verificación de Steam ID duplicadas)  
- [ ] Limpieza automática de imágenes de eventos finalizados  

---

### 📚 Fase 6 — Documentación y testing
- [ ] Documentar estructura de código y API  
- [ ] Escribir manual para creadores de eventos  
- [ ] Crear flujo de pruebas automatizadas con `pytest`

---

## 🧩 Tareas técnicas pendientes (TODOs del código)

### 🕒 Configuración de fechas y horas
- [ ] Implementar SelectMenus para fecha/hora (día, mes, año, hora, minuto)  
- [ ] Validar combinación y evitar fechas en el pasado  
- [ ] Convertir a UTC usando `zoneinfo` según zona horaria seleccionada  

---

### 🚗 Paso vehículos
- [ ] Abrir Modal solicitando vehículo(s)  
- [ ] Separar por coma  
- [ ] Limitar a 10 entradas  
- [ ] Validar longitud  
- [ ] Convertir a JSON y almacenar con `update_session(user_id, "vehicles", vehicles)`  
- [ ] Continuar al siguiente paso del wizard  

---

### 🏁 Paso seleccionar pista
- [ ] Consultar lista de pistas desde `track_db.get_all_tracks()`  
- [ ] Si no hay pistas, cancelar wizard con mensaje  
- [ ] Crear un SelectMenu con cada circuito  
- [ ] Guardar con `update_session(user_id, "track", track_id)`  
- [ ] Continuar al siguiente paso del wizard  

---

### 👥 Paso configuración de capacidad (slots)
- [ ] TextInput para `MAX_PILOTS` (entero positivo)  
- [ ] SelectMenu para `BROADCAST_SLOTS` (1–3)  
- [ ] Obtener `pit_slots` del track seleccionado  
- [ ] Validar que `(max_pilots + broadcast_slots) <= pit_slots`  
- [ ] Calcular automáticamente “teams” según la disponibilidad restante  
- [ ] Guardar todo en la sesión  
- [ ] Mostrar error si validación falla  

---

### 🧮 Paso cálculo de equipos
- [ ] Calcular capacidad real (`pit_slots - broadcast_slots`)  
- [ ] Generar combinaciones de equipos equilibradas  
- [ ] Guardar `team_count` y `team_size_list`  
- [ ] Asignar nombres y colores de equipos  
- [ ] Mostrar vista previa de distribución  
- [ ] Bloquear avance si no hay configuración válida  

---

### 🛡️ Paso asignación de roles y publicación
- [ ] Preguntar si se asignarán roles a pilotos o comisarios  
- [ ] Seleccionar roles existentes si aplica  
- [ ] Seleccionar canales de publicación  
- [ ] Validar duplicidades  
- [ ] Guardar en `session["data"]` los IDs de roles/canales  

---

### ⚖️ Paso normas, reglamento y skins
- [ ] Campo para normas especiales  
- [ ] Campo para reglamento (URL, canal o PDF)  
- [ ] Campo para skins personalizadas  
- [ ] Validaciones de contenido y formato  

---

### ✅ Paso final — Confirmación y persistencia
- [ ] Mostrar resumen completo del evento  
- [ ] Botones “Confirmar” y “Cancelar”  
- [ ] Guardar evento en DB (`event_db`)  
- [ ] Crear estructura de equipos  
- [ ] Confirmación al creador  
- [ ] Publicar embed en canal si aplica  
- [ ] Validar campos obligatorios antes de guardar  

---

## 🧠 Notas generales
- Toda acción debe verificar permisos del usuario/rol antes de ejecutarse.  
- Mantener cada módulo como *cog* independiente para facilitar mantenimiento.  
- Evitar dependencias innecesarias: usar solo `discord.py`, `aiosqlite`, `python-dotenv`.  
- Cada cambio relevante debe reflejarse aquí.

---

✏️ **Última actualización:** _Sincronizado con TODOs del código – 2025-10-31_
