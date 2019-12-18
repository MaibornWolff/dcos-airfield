from . import airfield, instance, proxy, notebook


def register_blueprints(app):
    airfield.register_blueprint(app)
    instance.register_blueprint(app)
    proxy.register_blueprint(app)
    notebook.register_blueprint(app)
