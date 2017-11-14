# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms.validators import InputRequired, Regexp


class RevisionForm(FlaskForm):
    diff_id = HiddenField(
        'diff_id', validators=[InputRequired(), Regexp('^[0-9]+$')]
    )
