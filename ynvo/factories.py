import factory
from django.contrib.auth.models import User

from ynvo.models import (
    Client,
    Comment,
    Fee,
    Invoice,
    Project,
    Task,
    Transmitter,
    Work,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "password")


class TransmitterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transmitter

    user = factory.SubFactory(UserFactory)
    name = factory.Faker("name")
    vat = factory.Faker("ssn")
    address = factory.Faker("address")
    zipcode = factory.Faker("zipcode")
    city = factory.Faker("city")
    payment = factory.Faker("text")


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    alias = factory.Faker("company")
    transmitter = factory.SubFactory(TransmitterFactory)
    name = factory.Faker("name")
    vat = factory.Faker("ssn")
    address = factory.Faker("address")
    zipcode = factory.Faker("zipcode")
    city = factory.Faker("city")


class InvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invoice

    invo_from = factory.SubFactory(TransmitterFactory)
    invo_to = factory.LazyAttribute(
        lambda obj: ClientFactory(transmitter=obj.invo_from)
    )


class FeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Fee

    invoice = factory.SubFactory(InvoiceFactory)
    ftype = "hour"
    activity = factory.Faker("sentence")
    price = factory.Faker("pyfloat", positive=True, max_value=200)
    amount = factory.Faker("pyfloat", positive=True, max_value=40)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    client = factory.SubFactory(ClientFactory)
    name = factory.Faker("sentence")
    price_per_hour = factory.Faker("pyfloat", positive=True, max_value=100)
    discount = 0.0


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    project = factory.SubFactory(ProjectFactory)
    name = factory.Faker("sentence")
    priority = factory.Faker("random_int", min=0, max=10)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    comment = factory.Faker("text")
    task = factory.SubFactory(TaskFactory)


class WorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Work

    amount = factory.Faker("pyfloat", positive=True, max_value=8)
    work_type = "hour"
    comment = factory.Faker("text")
    date = factory.Faker("date_object")
    task = factory.SubFactory(TaskFactory)
