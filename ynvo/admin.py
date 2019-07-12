from django.contrib import admin

from .models import (
    Client,
    Fee,
    Invoice,
    Transmitter,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('alias', 'name', 'vat', 'address', 'zipcode', 'city')
    #raw_id_fields = ('committee', 'contest')


@admin.register(Transmitter)
class TransmitterAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'vat', 'address', 'zipcode', 'city',
                    'payment')


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('ftype', 'activity', 'price', 'amount')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'number', 'year', 'invo_from', 'invo_to',
                    'project', 'currency', 'tax', 'taxname', 'reverse_tax',
                    'reverse_taxname', 'created', 'paid')
    filter_horizontal = ('fees',)
