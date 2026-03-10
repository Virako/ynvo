import pytest
from django.contrib.admin import AdminSite

from ynvo.admin import ClientAdmin, FeeAdmin, InvoiceAdmin, TransmitterAdmin
from ynvo.factories import ClientFactory, FeeFactory, InvoiceFactory, TransmitterFactory
from ynvo.models import Client, Fee, Invoice, Transmitter


@pytest.fixture
def user1_with_transmitter(django_user_model):
    user = django_user_model.objects.create_user(username="user1", password="user1")
    transmitter = TransmitterFactory(user=user)
    return user, transmitter


@pytest.fixture
def user2_with_transmitter(django_user_model):
    user = django_user_model.objects.create_user(username="user2", password="user2")
    transmitter = TransmitterFactory(user=user)
    return user, transmitter


@pytest.fixture
def admin_with_transmitter(admin_user):
    transmitter = TransmitterFactory(user=admin_user)
    return admin_user, transmitter


# Transmitter access


@pytest.mark.django_db
def test_superuser_can_access_all_transmitters(
    rf, admin_with_transmitter, user1_with_transmitter
):
    admin_user, _ = admin_with_transmitter

    rf.user = admin_user
    queryset = TransmitterAdmin(Transmitter, AdminSite()).get_queryset(rf)
    assert queryset.count() == 2


@pytest.mark.django_db
def test_user_can_access_to_owner_transmitter(rf, user1_with_transmitter):
    user, transmitter = user1_with_transmitter

    rf.user = user
    queryset = TransmitterAdmin(Transmitter, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == transmitter


# Invoice access


@pytest.mark.django_db
def test_superuser_can_access_all_invoices(
    rf, admin_with_transmitter, user1_with_transmitter
):
    admin_user, _ = admin_with_transmitter
    _, transmitter = user1_with_transmitter
    InvoiceFactory(invo_from=transmitter)
    InvoiceFactory(invo_from=transmitter)

    rf.user = admin_user
    queryset = InvoiceAdmin(Invoice, AdminSite()).get_queryset(rf)
    assert queryset.count() == 2


@pytest.mark.django_db
def test_user_can_access_to_owner_invoice(rf, user1_with_transmitter):
    user, transmitter = user1_with_transmitter
    invoice = InvoiceFactory(invo_from=transmitter)

    rf.user = user
    queryset = InvoiceAdmin(Invoice, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == invoice


@pytest.mark.django_db
def test_user2_cannot_access_to_user1_invoice(
    rf, user1_with_transmitter, user2_with_transmitter
):
    _, transmitter1 = user1_with_transmitter
    user2, _ = user2_with_transmitter
    InvoiceFactory(invo_from=transmitter1)

    rf.user = user2
    queryset = InvoiceAdmin(Invoice, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0


# Client access


@pytest.mark.django_db
def test_superuser_can_access_all_clients(
    rf, admin_with_transmitter, user1_with_transmitter
):
    admin_user, admin_transmitter = admin_with_transmitter
    _, user_transmitter = user1_with_transmitter
    ClientFactory(transmitter=admin_transmitter)
    ClientFactory(transmitter=user_transmitter)

    rf.user = admin_user
    queryset = ClientAdmin(Client, AdminSite()).get_queryset(rf)
    assert queryset.count() == 2


@pytest.mark.django_db
def test_user_can_access_to_owner_client(rf, user1_with_transmitter):
    user, transmitter = user1_with_transmitter
    client = ClientFactory(transmitter=transmitter)

    rf.user = user
    queryset = ClientAdmin(Client, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == client


@pytest.mark.django_db
def test_user2_cannot_access_to_user1_client(
    rf, user1_with_transmitter, user2_with_transmitter
):
    _, transmitter1 = user1_with_transmitter
    user2, _ = user2_with_transmitter
    ClientFactory(transmitter=transmitter1)

    rf.user = user2
    queryset = ClientAdmin(Client, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0


# Fee access


@pytest.mark.django_db
def test_superuser_can_access_all_fees(
    rf, admin_with_transmitter, user1_with_transmitter
):
    admin_user, admin_transmitter = admin_with_transmitter
    _, user_transmitter = user1_with_transmitter
    FeeFactory(invoice=InvoiceFactory(invo_from=admin_transmitter))
    FeeFactory(invoice=InvoiceFactory(invo_from=user_transmitter))

    rf.user = admin_user
    queryset = FeeAdmin(Fee, AdminSite()).get_queryset(rf)
    assert queryset.count() == 2


@pytest.mark.django_db
def test_user_can_access_to_owner_fee(rf, user1_with_transmitter):
    user, transmitter = user1_with_transmitter
    fee = FeeFactory(invoice=InvoiceFactory(invo_from=transmitter))

    rf.user = user
    queryset = FeeAdmin(Fee, AdminSite()).get_queryset(rf)
    assert queryset.count() == 1
    assert queryset.first() == fee


@pytest.mark.django_db
def test_user2_cannot_access_to_user1_fee(
    rf, user1_with_transmitter, user2_with_transmitter
):
    _, transmitter1 = user1_with_transmitter
    user2, _ = user2_with_transmitter
    FeeFactory(invoice=InvoiceFactory(invo_from=transmitter1))

    rf.user = user2
    queryset = FeeAdmin(Fee, AdminSite()).get_queryset(rf)
    assert queryset.count() == 0
