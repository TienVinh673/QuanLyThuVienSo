from flask import current_app


def get_facade():
    return current_app.extensions["facade"]
