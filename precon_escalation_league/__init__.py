import os

from flask import Flask
from . import db, precon_league


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'precon-league.sqlite'),
        MYSQL_HOST = "167.172.207.241",
        MYSQL_USER = "db.py",
        MYSQL_PASSWORD = "p82]L76Y4S$?",
        MYSQL_DATABASE = "Precon Escalation League",
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return 'Hello, World!'


    db.init_app(app)


    app.register_blueprint(precon_league.bp)

    return app