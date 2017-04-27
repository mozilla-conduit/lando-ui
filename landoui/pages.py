# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from flask import Blueprint, render_template

pages = Blueprint('page', __name__)


@pages.route('/')
def home():
    return render_template('home.html', name='Wavid Dalsh')
