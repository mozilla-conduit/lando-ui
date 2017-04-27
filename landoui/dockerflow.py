from flask import Blueprint, current_app

dockerflow = Blueprint('dockerflow', __name__)


@dockerflow.route('/')
@dockerflow.route('/dockerflow')
def show():
    if current_app.config['SECRET_KEY']:
        return 'True'
    else:
        return 'False'
