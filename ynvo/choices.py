from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskStatus(models.TextChoices):
    PENDING = "P", _("Pending")
    IN_PROGRESS = "I", _("In progress")
    FINISHED = "F", _("Finished")
    BLOCKED = "B", _("Blocked")
