# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import enum
import json

from json.decoder import JSONDecodeError
from typing import (
    Optional,
    Type,
)

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    Field,
    FieldList,
    HiddenField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
    widgets,
)
from wtforms.validators import (
    InputRequired,
    Regexp,
    optional,
)


class JSONDecodable:
    def __init__(
        self, decode_type: Optional[Type] = None, message: Optional[str] = None
    ):
        self.decode_type = decode_type
        self.message = message or "Field must be JSON decodable"

    def __call__(self, form: FlaskForm, field: Field):
        try:
            decoded = json.loads(field.data)
        except JSONDecodeError:
            raise ValidationError(self.message)

        if self.decode_type is not None and not isinstance(decoded, self.decode_type):
            raise ValidationError(self.message)

        return decoded


class LandingPath(JSONDecodable):
    def __init__(self, message: Optional[str] = None):
        super().__init__(decode_type=list, message=message)

    def __call__(self, form: FlaskForm, field: Field):
        decoded = super().__call__(form, field)

        if len(decoded) < 1:
            raise ValidationError(self.message)

        for i in decoded:
            if not (
                len(i) == 2
                and "revision_id" in i
                and isinstance(i["revision_id"], str)
                and "diff_id" in i
                and isinstance(i["diff_id"], int)
            ):
                raise ValidationError(self.message)


class TransplantRequestForm(FlaskForm):
    landing_path = HiddenField(
        "landing_path",
        validators=[
            InputRequired(message="A landing path is required"),
            LandingPath(message="Landing path must be a JSON array of path objects"),
        ],
    )
    confirmation_token = HiddenField("confirmation_token")
    flags = HiddenField(
        "flags", validators=[JSONDecodable(decode_type=list)], default=[]
    )


class SecApprovalRequestForm(FlaskForm):
    new_message = TextAreaField(
        "new_message",
        validators=[InputRequired(message="A valid commit message must be provided")],
    )
    revision_id = StringField(
        "revision_id",
        validators=[
            InputRequired(message="A valid Revision monogram must be provided"),
            Regexp("^D[0-9]+$"),
        ],
    )


class UpliftRequestForm(FlaskForm):
    """Form used to request uplift of a stack."""

    revision_id = StringField(
        "revision_id",
        validators=[
            InputRequired(message="A valid Revision monogram must be provided"),
            Regexp("^D[0-9]+$"),
        ],
    )
    repository = SelectField(
        "repository",
        coerce=str,
        validators=[
            InputRequired("An uplift repository is required."),
        ],
    )


class UserSettingsForm(FlaskForm):
    """Form used to provide the Phabricator API Token."""

    phab_api_token = StringField(
        "Phabricator API Token",
        validators=[
            optional(),
            Regexp("^api-[a-z0-9]{28}$", message="Invalid API Token format"),
        ],
    )
    reset_phab_api_token = BooleanField("Delete", default="")


class Status(enum.Enum):
    """Allowable statuses of a tree."""

    OPEN = "open"
    CLOSED = "closed"
    APPROVAL_REQUIRED = "approval required"

    @classmethod
    def to_choices(cls) -> list[tuple[str, str]]:
        """Return a list of choices for display."""
        return [(choice.value, choice.value.capitalize()) for choice in list(cls)]


class ReasonCategory(enum.Enum):
    """Allowable reasons for a Tree closure."""

    NO_CATEGORY = ""
    JOB_BACKLOG = "backlog"
    CHECKIN_COMPILE_FAILURE = "checkin_compilation"
    CHECKIN_TEST_FAILURE = "checkin_test"
    PLANNED_CLOSURE = "planned"
    MERGES = "merges"
    WAITING_FOR_COVERAGE = "waiting_for_coverage"
    INFRASTRUCTURE_RELATED = "infra"
    OTHER = "other"

    @classmethod
    def to_choices(cls) -> list[tuple[str, str]]:
        """Return a list of choices for display."""
        return [(choice.value, choice.to_display()) for choice in list(cls)]

    def to_display(self) -> str:
        """Return a human-readable version of the category."""
        return {
            ReasonCategory.NO_CATEGORY: "No Category",
            ReasonCategory.JOB_BACKLOG: "Job Backlog",
            ReasonCategory.CHECKIN_COMPILE_FAILURE: "Check-in compilation failure",
            ReasonCategory.CHECKIN_TEST_FAILURE: "Check-in test failure",
            ReasonCategory.PLANNED_CLOSURE: "Planned closure",
            ReasonCategory.MERGES: "Merges",
            ReasonCategory.WAITING_FOR_COVERAGE: "Waiting for coverage",
            ReasonCategory.INFRASTRUCTURE_RELATED: "Infrastructure related",
            ReasonCategory.OTHER: "Other",
        }[self]

    @classmethod
    def is_valid_for_backend(cls, value) -> bool:
        """Return `True` if `value` is a valid `ReasonCategory` to be submitted.

        All `ReasonCategory` members are valid except for `NO_CATEGORY` as that is
        implied by an empty `tags` key in the backend.
        """
        try:
            category = cls(value)
        except ValueError:
            return False

        if category == ReasonCategory.NO_CATEGORY:
            return False

        return True


class TreeStatusSelectTreesForm(FlaskForm):
    """Form used to select trees for updating."""

    trees = FieldList(
        StringField(
            "Trees",
            widget=widgets.HiddenInput(),
        ),
    )

    def validate_trees(self, field):
        """Validate that at least 1 tree was selected."""
        if not field.entries:
            raise ValidationError(
                "A selection of trees is required to update statuses."
            )


class TreeStatusUpdateTreesForm(FlaskForm):
    """Form used to update the state of a selection of trees."""

    trees = FieldList(
        StringField(
            "Trees",
            validators=[
                InputRequired("A selection of trees is required to update statuses.")
            ],
            widget=widgets.HiddenInput(),
        )
    )

    status = SelectField(
        "Status",
        choices=Status.to_choices(),
        validators=[InputRequired("A status is required.")],
    )

    reason = StringField("Reason")

    reason_category = SelectField(
        "Reason Category",
        choices=ReasonCategory.to_choices(),
    )

    remember_this_change = BooleanField(
        "Remember this change",
        default=True,
    )

    message_of_the_day = StringField("Message of the day")

    def validate_reason(self, field):
        """Validate that the reason field is required for non-open statuses."""
        reason_is_empty = not field.data

        if Status(self.status.data) == Status.CLOSED and reason_is_empty:
            raise ValidationError("Reason description is required to close trees.")

    def validate_reason_category(self, field):
        """Validate that the reason category field is required for non-open statuses."""
        category_is_empty = (
            not field.data or ReasonCategory(field.data) == ReasonCategory.NO_CATEGORY
        )

        if Status(self.status.data) == Status.CLOSED and category_is_empty:
            raise ValidationError("Reason category is required to close trees.")


class TreeCategory(enum.Enum):
    """Categories of the various trees.

    Note: the definition order is in order of importance for display in the UI.
    Note: this class also exists in Lando-UI, and should be updated in both places.
    """

    DEVELOPMENT = "development"
    RELEASE_STABILIZATION = "release_stabilization"
    TRY = "try"
    COMM_REPOS = "comm_repos"
    OTHER = "other"

    @classmethod
    def sort_trees(cls, item: dict) -> int:
        """Key function for sorting tree `dict`s according to category order."""
        return [choice.value for choice in list(cls)].index(item["category"])

    @classmethod
    def to_choices(cls) -> list[tuple[str, str]]:
        """Return a list of choices for display."""
        return [(choice.value, choice.to_display()) for choice in list(cls)]

    def to_display(self) -> str:
        """Return a human readable version of the category."""
        return " ".join(word.capitalize() for word in self.value.split("_"))


class TreeStatusNewTreeForm(FlaskForm):
    """Add a new tree to Treestatus."""

    tree = StringField(
        "Tree",
        validators=[InputRequired("A tree name is required.")],
    )

    category = SelectField(
        "Tree category",
        choices=TreeCategory.to_choices(),
        default=TreeCategory.OTHER.value,
    )


class TreeStatusRecentChangesForm(FlaskForm):
    """Modify a recent status change."""

    id = HiddenField("Id")

    reason = StringField("Reason")

    reason_category = SelectField(
        "Reason Category",
        choices=ReasonCategory.to_choices(),
    )

    restore = SubmitField("Restore")

    update = SubmitField("Update")

    discard = SubmitField("Discard")


class TreeStatusLogUpdateForm(FlaskForm):
    """Modify a log entry."""

    id = HiddenField("Id")

    reason = StringField("Reason")

    reason_category = SelectField(
        "Reason Category",
        choices=ReasonCategory.to_choices(),
    )
