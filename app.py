from flask import Flask, render_template
from database import init_db
from routes.ai_bp import ai_bp

#Here the blueprints would be imported from other modules so they can be registered

app = Flask(__name__)# Creates the central application object and flask app is initialized.


""" Here we are registering blueprints
# We enroll blueprints in an effort of decoupling various functional areas of the application.
These routes are assigned namespaces by the argument of the 'url prefix which is api'.
# between our json API endpoints and the HTML front end.
"""



# Handles AI features: Content generation and safety checking via Gemini API.
app.register_blueprint(ai_bp, url_prefix='/api')







@app.route('/')
def home():
    """
    Entry point for the Single Page Application (SPA)
    Which uses the css for styling
    """
    return render_template('index.html')

if __name__ == '__main__':

    """ 
    Over here database is initialized and it
     Ensures the SQLite schema (tables for posts, comments, reports) exists
     before the server starts accepting requests.
    """
    init_db()

    """ Over here server is started
    It is Running in debug mode for development to enable hot-reloading and detailed error logs.
     Note: Debug mode should be disabled in a production environment.
    """

    app.run(host="0.0.0.0")