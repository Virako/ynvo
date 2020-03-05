from django.contrib import admin
from django.utils.html import format_html

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
    list_display = ('number', 'proforma', 'year', 'total', 'currency', 'invo_to',
                    'project', 'created', 'paid', 'pdf_url')
    filter_horizontal = ('fees',)
    list_filter = ('invo_to', 'year')
    date_hierarchy = 'created'

    def pdf_url(self, obj):
        return format_html('<a target="_blank" href="/ynvo/{}/">GEN</a>', obj.number)
