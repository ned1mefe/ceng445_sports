from flask import Flask
from api.routes.teams import teams_bp
from api.routes.games import games_bp
from api.routes.cups import cups_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(teams_bp, url_prefix='/teams')
    app.register_blueprint(games_bp, url_prefix='/games')
    app.register_blueprint(cups_bp, url_prefix='/cups')
    
    return app