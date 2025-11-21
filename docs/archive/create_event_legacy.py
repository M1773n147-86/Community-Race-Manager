"""
Archivo: create_event_legacy.py
Ubicación: src/archive/

Descripción:
Versión preliminar del asistente de creación de eventos.
Este archivo se conserva como referencia técnica, ya que contiene el plan de flujo 
completo (con pasos detallados y validaciones) que guiará la implementación 
modular futura del sistema de eventos (wizard extendido).

El flujo actual fue reemplazado por la arquitectura modular en 
`wizards_general/` (views, modals, handlers), pero los comentarios y 
estructuras aquí documentadas servirán como blueprint para las próximas fases.
"""


import discord
from discord import app_commands, Interaction
from discord.ext import commands
from utils.wizard_session import EventWizardSession
from .steps.step_title import show_title_step


class CreateEventWizard(commands.Cog):
    """Comando principal para iniciar el asistente de creación de eventos."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="create_event", description="Crea un nuevo evento paso a paso.")
    async def create_event(self, interaction: discord.Interaction):
        """Comando principal para iniciar el asistente de creación de evento."""
        user_id = interaction.user.id

        # 🔒 Verificar si el usuario ya tiene una sesión activa
        if EventWizardSession.exists(user_id):
            await interaction.response.send_message(
                "⚠️ Ya tienes un asistente activo. Finalízalo o cancélalo antes de iniciar otro.",
                ephemeral=True
            )
            return

        # 🧭 Crear sesión nueva y registrar datos mínimos
        EventWizardSession.start(user_id)
        EventWizardSession.update(user_id, "guild_id", interaction.guild_id)
        EventWizardSession.update(user_id, "created_by", user_id)
        print(
            f"[SESSION] Nueva sesión de wizard creada para user_id={user_id}")

        # 🪄 Lanzar el primer paso del wizard (modal de título y descripción)
        try:
            from .steps.step_title import StepTitleModal
            modal = StepTitleModal()
            await interaction.response.send_modal(modal)
            print(
                f"[WIZARD] Modal de título enviado a {interaction.user.name}")
        except Exception as e:
            print(f"[ERROR] Fallo al mostrar StepTitleModal: {e}")
            try:
                await interaction.response.send_message(
                    f"❌ Error al iniciar el asistente: `{e}`",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    f"❌ Error al iniciar el asistente: `{e}`",
                    ephemeral=True
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(CreateEventWizard(bot))


# TODO: Implementar SelectMenus para fecha/hora (día, mes, año, hora, minuto)
# TODO: Validar combinación y evitar fechas en el pasado
# TODO: Convertir a UTC usando zoneinfo según zona horaria seleccionada
# TODO: Paso vehículos
# - Abrir Modal solicitando vehículo(s)
# - Separar por coma
# - Limitar a 10 entradas
# - Validar longitud
# - Convertir a JSON y almacenar con update_session(user_id, "vehicles", vehicles)
# - Continuar al siguiente paso del wizard
# TODO: Paso seleccionar pista
# - Consultar la lista de pistas desde track_db.get_all_tracks()
# - Si no hay pistas, cancelar wizard con mensaje
# - Crear un SelectMenu con cada circuito
# - Al seleccionar, guardar con update_session(user_id, "track", track_id)
# - Continuar al siguiente paso del wizard
# TODO: Paso configuración de capacidad (slots)
# - Mostrar TextInput para que el usuario introduzca MAX_PILOTS (entero positivo)
# - Mostrar SelectMenu para seleccionar BROADCAST_SLOTS (1–3)
# - Obtener pit_slots del track seleccionado
# - Validar que MAX_PILOTS sea un entero y > 0
# - Validar que (max_pilots + broadcast_slots) <= pit_slots
# - Calcular automáticamente "teams" según la disponibilidad restante
# - Guardar todo en la sesión con update_session()
# - Si validación falla, mostrar error y bloquear avance
# - NOTA: input manual permite soportar circuitos con 26, 31, 32, etc.
# TODO: Paso de configuración de fechas (Start Time & Check-In Close)
# - Obtener zona horaria previamente seleccionada de session
# - Mostrar un campo DateInput: día, mes, año
# - Mostrar TimeInput con intervalos de 15 minutos (00, 15, 30, 45)
# - Pre-cargar la fecha y hora actual del usuario (no permitir pasado)
# - Parsear con datetime + zoneinfo
# - Validar que la hora de inicio NO esté en el pasado
#
# Check-In Close:
# - Mostrar otro TimeInput con intervalos de 15 min
# - Restringirlo a máximo 3h antes del inicio
# - Validar que check-in close < start time
#
# Guardar en session:
#   start_datetime (ISO)
#   checkin_close_datetime (ISO)
#
# En caso de error de validación:
# - Bloquear avance
# - Mostrar mensaje explícito “la hora seleccionada no es válida”
# TODO: Paso de cálculo de equipos
# - Obtener desde session:
#       max_drivers (capacidad definida)
#       broadcast_slots (0-3)
#       track.pit_slots (desde track_db)
#
# - Calcular capacidad real:
#       real_capacity = track.pit_slots - broadcast_slots
#
# - Generar todas las combinaciones de equipos posibles:
#       - Equipos >= 2 pilotos
#       - Diferencia entre tamaños <= 1
#       - Usar la mayor cantidad de slots posible
#
# - Priorizar:
#       1. Distribución más equilibrada
#       2. Máximo uso de slots
#       3. Rellenar huecos restantes con broadcast si es necesario
#
# - Guardar en session["data"]:
#       team_count
#       team_size_list  # lista de tamaños de cada equipo
#
# - Mostrar al usuario vista previa:
#       "→ 29 pilotos se dividirán en 7 equipos de 4 y 1 equipo de 1 (ajustado)"
#
# - Bloquear avance si no se puede generar distribución válida
#
# - Asignación de nombres de equipos:
#       - Usar colores para equipos regulares: Rojo, Azul, Verde, Amarillo, etc.
#       - Si hay broadcast slots asignados, crear un "equipo broadcast" con emoji especial 🎥 o ⭐
#       - Esto se reflejará en la UI y en la lista de inscritos
#       - Garantizar consistencia con team_size_list
# TODO: Paso asignación de roles y publicación en canal
# - Piloto registrado:
#       - Preguntar si desea asignar rol (TRUE/FALSE)
#       - Si TRUE, seleccionar rol existente
#       - Guardar en session["data"]["registered_role_id"]
#
# - Comisario:
#       - Preguntar si hay rol de comisario (TRUE/FALSE)
#       - Si TRUE, seleccionar rol existente
#       - Guardar en session["data"]["marshal_role_id"]
#
# - Publicación de participantes/equipos:
#       - Preguntar si se publicará lista (TRUE/FALSE)
#       - Si TRUE, seleccionar canal existente
#       - Guardar en session["data"]["participants_channel_id"]
#
# - Publicación del evento:
#       - Preguntar si se publicará en canal específico (TRUE/FALSE)
#       - Si TRUE, seleccionar canal existente
#       - Si FALSE, usar integración interna del bot
#       - Guardar en session["data"]["event_channel_id"]
#
# - Validaciones:
#       - Comprobar existencia de roles y canales
#       - Evitar duplicidad de canales para distintas funciones
#       - Bloquear avance si selección no es válida
# TODO: Paso normas, reglamento y skins
# - Normas especiales:
#       - Preguntar si aplican (TRUE/FALSE)
#       - Si TRUE, campo de texto descriptivo
#       - Guardar en session["data"]["special_rules"]
#
# - Reglamento:
#       - Preguntar si aplica (TRUE/FALSE)
#       - Si TRUE, campo de texto para URL, canal o PDF
#       - Guardar en session["data"]["regulation"]
#
# - Skins personalizadas:
#       - Preguntar si se permite (TRUE/FALSE)
#       - Si TRUE, pedir enlace de subida
#       - Guardar en session["data"]["skins_url"]
#
# - Validaciones:
#       - No vacíos si TRUE
#       - Links deben tener formato válido
#       - Bloquear avance si no cumple
# TODO: Paso final — Confirmación y persistencia
# - Mostrar resumen completo del evento
# - Botones:
#       - Confirmar → guarda evento en DB (event_db)
#       - Cancelar → elimina session temporal
# - Guardar en DB:
#       - Todos los campos de session["data"]
#       - Marcar evento como activo
#       - Crear estructura de equipos (team_size_list + nombres/colores)
# - Mensajes finales:
#       - Ephemeral confirmación al creador
#       - Publicar embed en event_channel_id si corresponde
#       - Publicar lista de participantes/equipos si corresponde
# - Validaciones finales:
#       - Confirmar que todos los campos obligatorios estén completos
#       - Bloquear persistencia si falta algún dato crítico
