import uuid

from flask import json, Flask, request, g
from loguru import logger

from celery import Celery

from flask_session import Session
import redis
from authlib.integrations.flask_client import OAuth
from application.settings import FLASK_SECRET, ELASTIC_SEARCH_HOST, FLASK_SESSION_TYPE, FLASK_SESSION_REDIS, \
    CELERY_BROKER_URL, CELERY_RESULT_BACKEND, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD


def log_to_elasticsearch(record):
    """
    Sends a Loguru log record to Elasticsearch.

    Args:
        record (loguru.Record): The Loguru log record.
    """
    from elasticsearch import Elasticsearch
    es = Elasticsearch(
        hosts=[ELASTIC_SEARCH_HOST],
        http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
    )

    try:
        context_id = None
        entry_point = None
        try:
            context_id = g.get("context_id")
            entry_point = g.get("entry_point")
        except RuntimeError as e:
            pass
            # logger.error("Error accessing critical values of log", kv={'error': str(e)})

        # Extract relevant data from the record
        log_record = record.record
        log_data = {
            "message": log_record["message"],  # Access 'message' as an attribute
            "level": log_record["level"].name,  # Access 'level' as an attribute
            "timestamp": log_record["time"].isoformat(),  # Access 'time' as an attribute
            "file": log_record["file"].path,  # Access 'file' as an attribute
            "line": log_record["line"],  # Access 'line' as an attribute
            "function": log_record["function"],  # Access 'function' as an attribute
            "uri_path": entry_point,
            "request_id": context_id,
            # ... add other fields as needed ...
        }
        kv_pairs = log_record["extra"].get("kv", {})
        log_data.update(kv_pairs)

        # Send the log data to Elasticsearch
        es.index(index="my-flask-app-logs", document=log_data)

    except Exception as e:
        logger.error("Error sending log to Elasticsearch", kv={'error': str(e)})


def make_celery(app):
    """
    Creates a Celery application instance that is linked to the Flask application context.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        Celery: The Celery application instance.
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            task_id = self.request.id

            # Create an app context
            with app.app_context():
                g.context_id = task_id
                g.entry_point = self.name
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app() -> Flask:
    """
    Creates and configures the Flask application instance.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)

    # Session configuration
    app.secret_key = FLASK_SECRET
    app.config['SESSION_TYPE'] = FLASK_SESSION_TYPE
    app.config['SESSION_REDIS'] = redis.from_url(FLASK_SESSION_REDIS)
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800
    Session(app)

    # Celery configuration
    app.config.update(
        CELERY_BROKER_URL=CELERY_BROKER_URL,
        CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND,
        CELERY_IMPORTS=('workers.celery_tasks',),
        CELERY_DEFAULT_QUEUE='default',
    )

    # OAuth Google configuration
    oauth = OAuth(app)
    app.config['GOOGLE_OAUTH'] = oauth.register(
        name='google',
        client_id='YOUR_GOOGLE_CLIENT_ID',  # Replace with your actual client ID
        client_secret='YOUR_GOOGLE_CLIENT_SECRET',  # Replace with your actual client secret
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
    )

    @app.before_request
    def before_request():
        def generate_request_id():
            """Generates a unique request ID using UUID version 4."""
            return str(uuid.uuid4())

        g.context_id = generate_request_id()
        g.entry_point = request.path

    return app


# Create apps
flask_app = create_app()
celery_app = make_celery(flask_app)

# Register blueprints
from application.routes.orders import orders_blueprint
from application.routes.wallet import wallet_blueprint
from application.routes.user import user_blueprint
from application.routes.purchase_intent import purchase_intent_blueprint

flask_app.register_blueprint(wallet_blueprint)
flask_app.register_blueprint(user_blueprint)
flask_app.register_blueprint(orders_blueprint)
flask_app.register_blueprint(purchase_intent_blueprint)

# Stream logs to kibana
logger.add(log_to_elasticsearch, serialize=lambda record: json.dumps(record))


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=False, threaded=True, port=8080)

