# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
from json.decoder import JSONDecodeError

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, RadioField, StringField, \
    TextAreaField, ValidationError
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


class YesNoField(RadioField):
    """
    A simple boolean field displayed as a list of radio buttons
    Will output a bool value (or None on unknown)
    """

    def post_validate(self, *args, **kwargs):
        values = {'yes': True, 'no': False, 'unknown': None}
        self.data = values.get(self.data)


class SecureCommitMessageForm(FlaskForm):
    """Form used to submit a new commit message for sec-approval."""

    new_title = StringField(
        'Updated commit title',
        validators=[optional()],
    )

    new_summary = TextAreaField(
        'Updated commit summary (may be blank)',
        validators=[optional()],
    )

    def validate_new_summary(form, field):
        if not form.new_title.data:
            raise ValidationError(
                "You must also supply a commit message title."
            )


class SecApprovalRequestForm(SecureCommitMessageForm):
    """Form used to make a sec-approval request."""

    difficulty_of_constructing_exploit_from_patch = TextAreaField(
        'How easily could an exploit be constructed based on the patch?',
        validators=[InputRequired()],
    )

    patch_makes_flaw_obvious = YesNoField(
        'Do comments in the patch, the check-in comment, or tests included '
        'in the patch paint a bulls-eye on the security problem?',
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
            ('unknown', 'Unknown'),
        ],
        validators=[InputRequired()]
    )

    branches_affected_by_flaw = StringField(
        'Which older supported branches are affected by this flaw?',
        validators=[InputRequired()],
    )

    introduced_by_bug_number = StringField(
        'If the flaw does not affect all branches, which bug introduced the '
        'flaw?',
        validators=[
            optional(),
            Regexp(r'\d+', message='A number is required'),
        ],
    )

    author_has_backports_for_affected_branches = YesNoField(
        'Do you have backports for the affected branches?',
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        validators=[InputRequired()],
    )

    difficulty_of_backporting_fix = TextAreaField(
        'If you do not have backports, how different, hard to create, and '
        'risky will they be?',
        validators=[optional()],
    )

    risk_of_patch_causing_regression = TextAreaField(
        'How likely is this patch to cause regressions; how much testing does '
        'it need?',
        validators=[InputRequired()]
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
