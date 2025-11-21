"""
Archivo: discord_resources.py
Ubicación: src/cogs/events_wizard/

Descripción:
Contiene las funciones auxiliares para la creación de recursos internos de Discord 
durante el proceso de creación de eventos. Centraliza operaciones como la generación 
de roles, canales y eventos programados, utilizadas por los distintos pasos del 
wizard de eventos. Su propósito es desacoplar la lógica de infraestructura de Discord 
de la lógica de interacción del usuario.
"""

import discord
from discord import Guild, Role


class DiscordEventResources:
    """
    Clase que agrupa métodos estáticos y utilidades para crear los recursos
    necesarios en Discord durante la generación de un nuevo evento.
    """

    @staticmethod
    async def create_event_role(guild: Guild, name: str) -> Role:
        """
        Crea un rol temporal asociado a un evento. El nombre del rol incluye
        un identificador único basado en el timestamp para evitar duplicados.
        """
        role_name = f"event-{int(discord.utils.time_snowflake())}"
        return await guild.create_role(
            name=role_name,
            mentionable=False,
            reason="Rol temporal generado para evento automatizado"
        )

    @staticmethod
    async def create_event_channel(guild: Guild, name: str, role: Role):
        """
        Crea un canal de texto privado para el evento con permisos asignados
        al rol del evento. Solo los usuarios con dicho rol podrán acceder.
        """
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(
                view_channel=True, send_messages=True
            ),
        }
        return await guild.create_text_channel(
            name=f"evento-{name.replace(' ', '-').lower()[:50]}",
            overwrites=overwrites,
            reason="Canal temporal generado para evento"
        )

    @staticmethod
    async def create_discord_event(
        guild: Guild,
        name: str,
        start_time,
        description: str | None = None,
        location: str | None = None,
        channel=None
    ):
        """
        Crea un evento programado de Discord vinculado al evento del wizard.
        """
        return await guild.create_scheduled_event(
            name=name,
            start_time=start_time,
            description=description or "",
            entity_type=discord.EntityType.voice,
            channel=channel,
            entity_metadata=discord.ScheduledEventEntityMetadata(
                location=location
            ) if location else None,
            reason="Evento programado generado por wizard"
        )
