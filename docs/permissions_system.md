# Sistema de Autorizaciones Internas — Community Race Manager

## Descripción General
El sistema de permisos internos define qué usuarios o roles pueden ejecutar comandos
del bot **Community Race Manager** dentro de cada servidor de Discord.

Por defecto, **solo el propietario del servidor** tiene acceso total a los comandos
de la aplicación. A través del módulo `moderation_crm`, puede delegar permisos
añadiendo o eliminando roles o usuarios específicos.

---

## Estructura de Base de Datos

### Tabla: `authorized_entities`
| Campo | Tipo | Descripción |
|-------|------|--------------|
| `guild_id` | INTEGER | ID del servidor de Discord. |
| `entity_id` | INTEGER | ID del usuario o rol autorizado. |
| `entity_type` | TEXT | Tipo de entidad (`user` o `role`). |

**Restricciones:**
- Combinación única `(guild_id, entity_id, entity_type)`.

---

## Funciones Clave en `database/db.py`

| Método | Descripción |
|--------|--------------|
| `add_authorized_entity(guild_id, entity_id, entity_type)` | Registra una entidad como autorizada. |
| `remove_authorized_entity(guild_id, entity_id, entity_type)` | Elimina una entidad autorizada. |
| `is_authorized(guild_id, module, user)` | Verifica si un usuario o alguno de sus roles está autorizado. |

---

## Comandos de Moderación Relacionados
Los siguientes comandos están implementados en `src/cogs/moderation_crm/commands.py`:

| Comando | Descripción |
|----------|-------------|
| `/add_role` | Autoriza un rol para usar la APP. |
| `/add_user` | Autoriza un usuario. |
| `/remove_role` | Revoca la autorización de un rol. |
| `/remove_user` | Revoca la autorización de un usuario. |

Todos los comandos están **restringidos al propietario del servidor** y envían
respuestas **ephemeral** para evitar exposición de información sensible.

---

## Flujo de Autorización
1. El propietario ejecuta `/add_role` o `/add_user`.
2. La entidad se registra en la tabla `authorized_entities`.
3. Cuando un usuario ejecuta un comando de la APP:
   - Si es el propietario, se autoriza automáticamente.
   - Si su ID o alguno de sus roles está registrado, el comando se ejecuta.
   - Si no, la acción se deniega.

---

## Próximas Extensiones
- Permisos por módulo (campo `module_name` futuro).
- Comando `/list_authorized` para mostrar roles y usuarios actuales.
- Integración con ticketing para gestión de acceso temporal.
