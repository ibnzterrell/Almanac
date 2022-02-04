from dotenv import load_dotenv
from flask import Flask, g
from flask_cors import CORS
from model.DB import db_connect, db_disconnect
from api.headline_route import headlineAPI
from api.search_route import searchAPI

load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def defaultRoute():
    return "OK"

@app.route("/warmup", methods=["GET"])
def warmupRoute():
    db_connect()
    return "OK"

@app.route("/health", methods=["GET"])
def healthRoute():
    return "OK"

# Close database on shutdown
@app.teardown_appcontext
def shutdown(exception):
    db_disconnect()

app.register_blueprint(headlineAPI)
app.register_blueprint(searchAPI)

CORS(app)
if __name__ == '__main__':
    app.run(port=80, host='0.0.0.0', debug=True)