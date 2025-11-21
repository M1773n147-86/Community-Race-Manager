import pytest
import asyncio

# Simulación de imports de entorno del bot
from cogs.wizard.managers import track_list_manager


@pytest.mark.asyncio
async def test_show_track_list_manager(monkeypatch):
    """Verifica que el gestor de listas de circuitos se inicializa correctamente."""

    class MockInteraction:
        def __init__(self):
            self.user = type("User", (), {"id": 1})()

        async def response_send_message(self, content, view, ephemeral):
            assert "Gestor de listas de circuitos" in content
            assert view is not None
            assert ephemeral is True

        # Alias para coincidir con el método real
        @property
        def response(self):
            class Response:
                async def send_message(_, content, view=None, ephemeral=False):
                    assert "Gestor de listas de circuitos" in content
                    assert view is not None
                    assert ephemeral is True
            return Response()

    mock_interaction = MockInteraction()

    await track_list_manager.show_track_list_manager(mock_interaction)
    print("✅ test_show_track_list_manager ejecutado correctamente.")


def test_view_buttons_existence():
    """Verifica que los botones principales existen en la vista."""
    view = track_list_manager.TrackListManagerView(user_id=1)

    button_labels = [item.label for item in view.children]
    assert "🆕 Crear lista" in button_labels
    assert "✏️ Editar lista" in button_labels
    assert "🗑️ Eliminar lista" in button_labels
    assert "↩️ Volver al asistente" in button_labels

    print("✅ test_view_buttons_existence ejecutado correctamente.")
