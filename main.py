from app.routes.auth_routes import auth_bp
from app.routes.signup_routes import signup_bp
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app,origins="*")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(signup_bp)

if __name__ == '__main__':
    app.run(debug=True)
