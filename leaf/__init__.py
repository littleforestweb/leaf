from flask import Flask

from leaf.config import Config
from leaf.decorators import limiter
from leaf.deployments.routes import deployments
from leaf.editor.routes import editor
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




def create_app(config_class=Config):
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

    return app
