# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
from json.decoder import JSONDecodeError

from flask_wtf import FlaskForm
from wtforms import HiddenField, ValidationError
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


class JSONDecodable:
    def __init__(self, decode_type=None, message=None):
        self.decode_type = decode_type
        self.message = message or 'Field must be JSON decodable'

    def __call__(self, form, field):
        try:
            decoded = json.loads(field.data)
        except JSONDecodeError:
            raise ValidationError(self.message)

        if (
            self.decode_type is not None and
            not isinstance(decoded, self.decode_type)
        ):
            raise ValidationError(self.message)

        return decoded


class LandingPath(JSONDecodable):
    def __init__(self, message=None):
        super().__init__(decode_type=list, message=message)

    def __call__(self, form, field):
        decoded = super().__call__(form, field)

        if len(decoded) < 1:
            raise ValidationError(self.message)

        for i in decoded:
            if not (
                len(i) == 2 and 'revision_id' in i and
                isinstance(i['revision_id'], str) and 'diff_id' in i and
                isinstance(i['diff_id'], int)
            ):
                raise ValidationError(self.message)


class TransplantRequestForm(FlaskForm):
    landing_path = HiddenField(
        'landing_path',
        validators=[
            InputRequired(message='A landing path is required'),
            LandingPath(
                message='Landing path must be a JSON array of path objects'
            ),
        ],
    )
    confirmation_token = HiddenField('confirmation_token')
