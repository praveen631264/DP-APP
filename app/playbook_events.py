
from flask import current_app
from app.socket_instance import socketio
from app.database import db
from app.blueprints.playbooks import PlaybookModel

@socketio.on('create_playbook')
def handle_create_playbook(data):
    """Handles the create_playbook event."""
    try:
        validated_data = PlaybookModel(**data).dict()
        playbook_id = db.create_playbook(validated_data)
        playbook = db.get_playbook(playbook_id)
        socketio.emit('playbook_updated', playbook)
    except Exception as e:
        current_app.logger.error(f'Error creating playbook: {e}', exc_info=True)

@socketio.on('update_playbook')
def handle_update_playbook(data):
    """Handles the update_playbook event."""
    try:
        playbook_id = data.pop('id')
        validated_data = PlaybookModel(**data).dict()
        db.update_playbook(playbook_id, validated_data)
        updated_playbook = db.get_playbook(playbook_id)
        socketio.emit('playbook_updated', updated_playbook)
    except Exception as e:
        current_app.logger.error(f'Error updating playbook: {e}', exc_info=True)

@socketio.on('delete_playbook')
def handle_delete_playbook(data):
    """Handles the delete_playbook event."""
    try:
        playbook_id = data.get('id')
        db.delete_playbook(playbook_id)
        socketio.emit('playbook_deleted', {'id': playbook_id})
    except Exception as e:
        current_app.logger.error(f'Error deleting playbook: {e}', exc_info=True)
