# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
from json.decoder import JSONDecodeError
import logging

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, StringField, TextAreaField, \
    ValidationError, RadioField, SelectMultipleField
from wtforms.validators import Required, InputRequired, optional, Regexp
from wtforms.widgets import ListWidget, CheckboxInput

logger = logging.getLogger(__name__)


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


class RepositoriesField(SelectMultipleField):
    """
    Form field to select one or more Phabricator repositories
    using a list of checkboxes
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

    # Select at least one repository
    validators = [Required(message='Please select a repository')]

    def process_data(self, repositories=[], *args, **kwargs):
        # Populate initial data using the repositories slugs from the view
        self.choices = [(repo, repo) for repo in repositories]


class YesNoField(RadioField):
    """
    A simple boolean field displayed as a list of radio buttons
    Will output a bool value (or None on unknown)
    """

    def post_validate(self, *args, **kwargs):
        values = {'yes': True, 'no': False, 'unknown': None}
        self.data = values.get(self.data)


class BugsField(StringField):
    """
    Convert a string into a list of bugs
    """

    def post_validate(self, *args, **kwargs):
        # TODO: check those are valid bugs
        self.data = [value.strip() for value in self.data.split(',')]


class UpliftRequestForm(FlaskForm):
    """Form to create a new uplift request"""
    repositories = RepositoriesField('Repository to request uplift')

    user_impact = TextAreaField(
        'User impact if declined', validators=[
            InputRequired(),
        ]
    )

    steps_to_reproduce = TextAreaField(
        'If yes, steps to reproduce', validators=[]
    )

    risky = TextAreaField(
        'Why is the change risky/not risky? (and alternatives if risky)',
        validators=[
            InputRequired(),
        ]
    )

    automated_tests = YesNoField(
        'Is this code covered by automated tests ?',
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
            ('unknown', 'Unknown'),
        ],
    )

    nightly = YesNoField(
        'Has the fix been verified in Nightly ?',
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
    )

    manual_qe = YesNoField(
        'Needs manual test from QE ?',
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
    )

    bug_ids = BugsField(
        'List of other uplifts needed',
    )

    risk = RadioField(
        'Risk to taking this patch',
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ]
    )

    string_changes = StringField(
        'String changes made/needed',
    )
