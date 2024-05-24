import os
import logging

from flask import Flask

from leaf.config import Config
from leaf.decorators import limiter
from leaf.deployments.routes import deployments
from leaf.editor.routes import editor
from leaf.files_manager.routes import files_manager
from leaf.groups.routes import groups
from leaf.lists.routes import lists
from leaf.main.routes import main
from leaf.menus.routes import menus
from leaf.pages.routes import pages
from leaf.serverside.saml import saml_route
from leaf.sites.routes import sites
from leaf.template_editor.routes import template_editor
from leaf.users.routes import users
from leaf.workflow.routes import workflow
from leaf.workflow.models import check_if_should_publish_items
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import gc


def check_db():
    """
    Ensures that the database structure matches the expected schema defined in 'db_structure.sql'.

    This function connects to the database, reads SQL statements from 'db_structure.sql',
    executes each statement, commits changes, and closes the database connection.

    Raises:
        Any exceptions raised during database connection, SQL execution, or file reading.

    """

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    # Read SQL File
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_structure.sql")) as in_file:
        sql_content = in_file.read()

    # Check if required tables exist
    sql_statements = [sql_statement.strip() for sql_statement in sql_content.split(';')]
    for sql_statement in sql_statements:
        mycursor.execute(sql_statement)
    mydb.commit()

    # Get table names from SQL script
    required_table_names = []
    for idx, line in enumerate(sql_content.split("\n")):
        if line.strip().startswith('CREATE TABLE IF NOT EXISTS'):
            table_name = line.split('`')[1]
            required_table_names.append(table_name)
    required_table_names = sorted(required_table_names)

    # Get table names from Live DB
    ignore_table_names = ["account_"]
    mycursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", ("leaf",))
    live_table_names = [table[0] for table in mycursor.fetchall() if not any(table[0].startswith(prefix) for prefix in ignore_table_names)]
    live_table_names = sorted(live_table_names)

    # Drop unused tables
    drop_tables = [table for table in live_table_names if table not in required_table_names]
    for table_name in drop_tables:
        mycursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Close DB Connection
    mydb.close()


def create_app(config_class=Config):
    """
    Creates and configures the Flask application.

    Args:
        config_class: Configuration class for the Flask application.

    Returns:
        app: Initialized Flask application instance.

    """

    app = Flask(__name__)
    limiter.init_app(app)
    app.config.from_object(Config)

    # Register Blueprints
    app.register_blueprint(main)
    app.register_blueprint(sites)
    app.register_blueprint(pages)
    app.register_blueprint(users)
    app.register_blueprint(groups)
    app.register_blueprint(lists)
    app.register_blueprint(menus)
    app.register_blueprint(deployments)
    app.register_blueprint(workflow)
    app.register_blueprint(editor)
    app.register_blueprint(template_editor)
    app.register_blueprint(saml_route)
    app.register_blueprint(files_manager)

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_if_should_publish_items, trigger="interval", minutes=5)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    # Optional: Force garbage collection
    atexit.register(lambda: gc.collect())

    # Check Database Integrity
    check_db()

    return app
