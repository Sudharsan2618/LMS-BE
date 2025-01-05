from app.routes.auth_routes import auth_bp
from app.routes.signup_routes import signup_bp
from flask import Flask

app = Flask(__name__)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(signup_bp)

if __name__ == '__main__':
    app.run(debug=True)
