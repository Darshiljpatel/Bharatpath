import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bharatpath-secret-2026')
    
    # Register Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.explorer_routes import explorer_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.nlp_routes import nlp_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(explorer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(nlp_bp)
    
    return app
