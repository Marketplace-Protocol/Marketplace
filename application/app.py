from flask import json, Flask
from loguru import logger

from application.routes.orders import orders_blueprint
from application.routes.wallet import wallet_blueprint
from application.routes.offers import offers_blueprint
from application.routes.user import user_blueprint

app = Flask(__name__)

app.register_blueprint(wallet_blueprint)
app.register_blueprint(offers_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(orders_blueprint)

# log file
logger.add("job.log", format="{time} - {message}")

@app.route("/hello_world")
def hello_world():
    logger.info('hello world')
    res = {'hello': 'world'}
    return json.dumps(res), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True, port=5000)

