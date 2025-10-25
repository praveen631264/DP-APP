from app import create_app

app, celery = create_app()

if __name__ == '__main__':
    # In a real production environment, you would use a production-ready WSGI server
    # like Gunicorn or uWSGI instead of the Flask development server.
    # Example with Gunicorn: gunicorn --worker-class eventlet -w 1 main:app
    from app.realtime_events import socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)