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
from app.routes.user_details_route import userdetails_bp
from app.routes.jobs_routes import jobs_bp
from app.routes.assessment_submission_routes import assessment_submission_bp
from app.routes.key_generation_routes import key_generation_bp
from app.routes.course_routes import course_bp as course_management_bp
from app.routes.admin_routes import admin_bp
from app.routes.qc_batch_routes import qc_batch_bp
from app.routes.ai_route import ai_bp
from app.routes.content_generate_route import content_generate_bp
from app.routes.transaction_view_route import transaction_view_bp
from app.routes.ppt_url_routes import ppt_url_bp
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://www.companion-lms.com"])
# CORS(app, origins=["http://localhost:3000"])

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
app.register_blueprint(userdetails_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(assessment_submission_bp)
app.register_blueprint(key_generation_bp)
app.register_blueprint(course_management_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(qc_batch_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(content_generate_bp)
app.register_blueprint(transaction_view_bp)
app.register_blueprint(ppt_url_bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
