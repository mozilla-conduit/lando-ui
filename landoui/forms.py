# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
from json.decoder import JSONDecodeError

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, StringField, TextAreaField, \
    ValidationError
from wtforms.validators import InputRequired, optional, Regexp


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


class SecApprovalRequestForm(FlaskForm):
    new_message = TextAreaField(
        'new_message',
        validators=[
            InputRequired(message='A valid commit message must be provided'),
        ]
    )
    revision_id = StringField(
        'revision_id',
        validators=[
            InputRequired(
                message='A valid Revision monogram must be provided'
            ),
            Regexp("^D[0-9]+$"),
        ]
    )


class UserSettingsForm(FlaskForm):
    """Form used to provide the Phabricator API Token."""
    phab_api_token = StringField(
        'Phabricator API Token',
        validators=[
            optional(),
            Regexp('^api-[a-z0-9]{28}$', message='Invalid API Token format')
        ]
    )
    reset_phab_api_token = BooleanField('Delete', default="")
