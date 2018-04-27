# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms.validators import InputRequired, Regexp


class RevisionForm(FlaskForm):
    diff_id = HiddenField(
        'diff_id',
        validators=[
            InputRequired(message='Diff Id is required'),
            Regexp('\A[0-9]+\Z', message='Diff Id must be a number')
        ]
    )
    confirmation_token = HiddenField('confirmation_token')
