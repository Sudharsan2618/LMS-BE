from app.routes.auth_routes import auth_bp
from app.routes.signup_routes import signup_bp
from app.routes.questions_routes import initial_assessment_questions_bp
from app.routes.initial_assessment_response_route import initial_assessment_responses_bp
from app.routes.home_header_routes import home_bp
from app.routes.course_master_routes import course_bp, courseenrollment_bp
from app.routes.user_persona_routes import user_bp
from app.routes.initial_assessment_route import user_initial_assessment_bp
from app.routes.course_master_routes import userenrollment_bp
from app.routes.ebook_routes import ebook_bp
from app.routes.course_content_route import course_content_bp
from app.routes.course_assessment_route import course_assessment_bp
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app,origins="*")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(signup_bp)
app.register_blueprint(initial_assessment_questions_bp)
app.register_blueprint(initial_assessment_responses_bp)
app.register_blueprint(home_bp)
app.register_blueprint(course_bp)
app.register_blueprint(user_bp)
app.register_blueprint(user_initial_assessment_bp)
app.register_blueprint(courseenrollment_bp)
app.register_blueprint(userenrollment_bp)
app.register_blueprint(ebook_bp)
app.register_blueprint(course_content_bp)
app.register_blueprint(course_assessment_bp)

if __name__ == '__main__':
    app.run(debug=True)
