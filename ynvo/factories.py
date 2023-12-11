import factory

from ynvo.models import (
    PersonalData,
    Client,
    Transmitter,
    Invoice,
    Fee,
    Project,
    Task,
    Comment,
    Work,
)


class PersonalDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonalData

    name = factory.Faker("name")
    vat = factory.Faker("vat")
    address = factory.Faker("address")
    zipcode = factory.Faker("zipcode")
    city = factory.Faker("city")


class TransmitterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transmitter

    payment = factory.Faker("text")


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    alias = factory.Faker("name")
    transmitter = factory.SubFactory(TransmitterFactory)
    name = factory.Faker("name")
    vat = factory.Faker("vat")
    address = factory.Faker("address")
    zipcode = factory.Faker("zipcode")
    city = factory.Faker("city")


class InvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invoice

    invo_from = factory.SubFactory(TransmitterFactory)
    invo_to = factory.SubFactory(ClientFactory)


class FeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Fee

    ftype = factory.Faker("text")
    activity = factory.Faker("text")
    price = factory.Faker("text")
    amount = factory.Faker("text")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Faker("text")


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    name = factory.Faker("text")


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    text = factory.Faker("text")


class WorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Work

    text = factory.Faker("text")
