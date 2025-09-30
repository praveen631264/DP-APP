import os
from app import create_app
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.health import health_bp
from app.blueprints.document import document_bp

# create_app() now returns both the app and the celery instance
app, celery = create_app()

app.register_blueprint(dashboard_bp)
app.register_blueprint(health_bp)
app.register_blueprint(document_bp)

if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
