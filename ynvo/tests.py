import pytest
from django.contrib.admin import AdminSite

from ynvo.admin import TransmitterAdmin, InvoiceAdmin, ClientAdmin, FeeAdmin
from ynvo.factories import TransmitterFactory, InvoiceFactory, ClientFactory, FeeFactory
from ynvo.models import Transmitter, Invoice, Client, Fee


# Transmitter access

@pytest.fixture
def transmitter_admin():
    return TransmitterAdmin(Transmitter, AdminSite())


def test_superuser_can_access_all_transmitters(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    transmitters = [
        TransmitterFactory(user=admin_user),
        TransmitterFactory(user=user),
    ]

    rf.user = admin_user
    queryset = TransmitterAdmin(Transmitter, AdminSite()).get_queryset(rf)
    assert queryset.count() == len(transmitters)


def test_user_can_access_to_owner_transmitter(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    transmitter = TransmitterFactory(user=user)

    rf.user = user
    queryset = TransmitterAdmin(Transmitter, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == transmitter


def test_user2_cannot_access_to_user1_transmitter(rf, django_user_model):
    user1 = django_user_model.objects.create_user(username="user1", password="user1")
    user2 = django_user_model.objects.create_user(username="user2", password="user2")
    TransmitterFactory(user=user1)

    rf.user = user2
    queryset = TransmitterAdmin(Transmitter, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0


# Invoice access

@pytest.fixture
def invoice_admin():
    return InvoiceAdmin(Invoice, AdminSite())


def test_superuser_can_access_all_invoices(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    transmitter = TransmitterFactory(user=user)
    invoices = [
        InvoiceFactory(invo_from=transmitter),
        InvoiceFactory(invo_from=transmitter),
    ]

    rf.user = admin_user
    queryset = InvoiceAdmin(Invoice, AdminSite()).get_queryset(rf)
    assert queryset.count() == len(invoices)


def test_user_can_access_to_owner_invoice(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    transmitter = TransmitterFactory(user=user)
    invoice = InvoiceFactory(invo_from=transmitter)

    rf.user = user
    queryset = InvoiceAdmin(Invoice, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == invoice


def test_user2_cannot_access_to_user1_invoice(rf, django_user_model):
    user1 = django_user_model.objects.create_user(username="user1", password="user1")
    user2 = django_user_model.objects.create_user(username="user2", password="user2")
    transmitter = TransmitterFactory(user=user1)
    InvoiceFactory(invo_from=transmitter)

    rf.user = user2
    queryset = InvoiceAdmin(Invoice, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0


# Client access

@pytest.fixture
def client_admin():
    return ClientAdmin(Client, AdminSite())


def test_superuser_can_access_all_clients(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    clients = [
        ClientFactory(user=admin_user),
        ClientFactory(user=user),
    ]

    rf.user = admin_user
    queryset = ClientAdmin(Client, AdminSite()).get_queryset(rf)
    assert queryset.count() == len(clients)


def test_user_can_access_to_owner_client(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    client = ClientFactory(user=user)

    rf.user = user
    queryset = ClientAdmin(Client, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == client


def test_user2_cannot_access_to_user1_client(rf, django_user_model):
    user1 = django_user_model.objects.create_user(username="user1", password="user1")
    user2 = django_user_model.objects.create_user(username="user2", password="user2")
    ClientFactory(user=user1)

    rf.user = user2
    queryset = ClientAdmin(Client, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0


# Fee access

@pytest.fixture
def fee_admin():
    return FeeAdmin(Fee, AdminSite())


def test_superuser_can_access_all_fees(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    fees = [
        FeeFactory(user=admin_user),
        FeeFactory(user=user),
    ]

    rf.user = admin_user
    queryset = FeeAdmin(Fee, AdminSite()).get_queryset(rf)
    assert queryset.count() == len(fees)


def test_user_can_access_to_owner_fee(rf, admin_user, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="user")
    fee = FeeFactory(user=user)

    rf.user = user
    queryset = FeeAdmin(Fee, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == fee


def test_user2_cannot_access_to_user1_fee(rf, django_user_model):
    user1 = django_user_model.objects.create_user(username="user1", password="user1")
    user2 = django_user_model.objects.create_user(username="user2", password="user2")
    FeeFactory(user=user1)

    rf.user = user2
    queryset = FeeAdmin(Fee, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0
