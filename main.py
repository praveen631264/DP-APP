from app import create_app

# create_app() returns both the app and the celery instance
app, celery = create_app()

if __name__ == "__main__":
    # The app is already configured and blueprints are registered
    # by the create_app function.
    # We can run it directly.
    app.run(debug=True, host="0.0.0.0", port=5000)
