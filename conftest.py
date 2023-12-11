import pytest
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from ynvo.models import (
    Client,
    Fee,
    Invoice,
    Transmitter,
    Project,
    Task,
    Comment,
    Work,
)


@pytest.fixture
def transmitter_group():
    models = [Transmitter, Client, Invoice, Fee, Project, Task, Comment, Work]
    content_types = []
    for model in models:
        content_types.append(ContentType.objects.get_for_model(model))
    permissions = Permission.objects.filter(content_type__in=content_types)
    group = Group.objects.get_or_create(name="transmitter")
    group.permissions.set(permissions)
    yield group


@pytest.fixture
def client_group():
    models = [Client, Project, Task, Comment, Work]
    content_types = []
    for model in models:
        content_types.append(ContentType.objects.get_for_model(model))
    permissions = Permission.objects.filter(content_type__in=content_types)
    group = Group.objects.get_or_create(name="transmitter")
    group.permissions.set(permissions)
    yield Group.objects.get_or_create(name="client")
