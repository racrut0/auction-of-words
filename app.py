import os

from flask import Flask, g, render_template

import auth


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")
    app.config["DATABASE"] = os.path.join(app.instance_path, "auction.db")
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(auth.close_db)
    app.register_blueprint(auth.bp)
    with app.app_context():
        auth.init_db()

    @app.route("/")
    @auth.login_required
    def lobby():
        # Заглушка: экран лобби делается в отдельной задаче (US-07, US-08).
        return render_template("lobby.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
