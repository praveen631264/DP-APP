
import os
from flask import Flask
from app.socket_instance import socketio
from app.blueprints.playbooks import playbooks_bp
from app.blueprints.dashboard import bp as dashboard_bp
from app.blueprints.documents import bp as documents_bp
from app.database import db
import app.playbook_events

app = Flask(__name__)

# Database configuration
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/my-project')
db.init_app(app)

# Register blueprints
app.register_blueprint(playbooks_bp, url_prefix='/api/v1/playbooks')
app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
app.register_blueprint(documents_bp, url_prefix='/api/v1/documents')


# SocketIO configuration
socketio.init_app(app, cors_allowed_origins='*')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
