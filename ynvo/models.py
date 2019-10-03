from django.db import models
from django.contrib.auth.models import User


class PersonalData(models.Model):
    name = models.CharField(max_length=128)
    vat = models.CharField(max_length=32)
    address = models.CharField(max_length=128)
    zipcode = models.CharField(max_length=16)
    city = models.CharField(max_length=64)

    class Meta:
        abstract = True


class Client(PersonalData):
    alias = models.CharField(max_length=32)

    def __str__(self):
        return self.alias


class Transmitter(PersonalData):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    payment = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Fee(models.Model):
    FEE_TYPES = (
        ('hour', 'hour'),
        ('unit', 'unit'),
        ('total', 'total'),
    )

    ftype = models.CharField(max_length=8, choices=FEE_TYPES, default='hour')
    activity = models.CharField(max_length=256)
    price = models.FloatField()
    amount = models.IntegerField(default=1)

    def __str__(self):
        return '{}: {} x {}'.format(self.ftype, self.price, self.amount)


class Invoice(models.Model):
    INVO_STATUS = (
        ('created', 'created'),
        ('send', 'send'),
        ('received', 'received'),
    )

    prefix = models.CharField(max_length=32, blank=True, null=True)
    number = models.PositiveIntegerField()
    year = models.PositiveIntegerField(blank=True, null=True)
    invo_from = models.ForeignKey(Transmitter, on_delete=models.PROTECT)
    invo_to = models.ForeignKey(Client, on_delete=models.PROTECT)
    fees = models.ManyToManyField(Fee, related_name='invoices')
    project = models.CharField(max_length=128, default='', blank=True)
    currency = models.CharField(max_length=4, default='€')
    extra_currency = models.CharField(max_length=4, blank=True, null=True)
    currency_exchange = models.FloatField(default=1.0)
    tax = models.IntegerField(default=21)
    taxname = models.CharField(max_length=16, default='IVA')
    reverse_tax = models.IntegerField(default=15)
    reverse_taxname = models.CharField(max_length=16, default='IRPF')
    note = models.TextField(blank=True, null=True)
    created = models.DateField(auto_now_add=True, blank=True, null=True,
            editable=True)
    paid = models.DateField(blank=True, null=True)
    proforma = models.BooleanField(default=False)

    def get_totals(self):
        subtotal = 0
        t_tax = 0
        t_reverse_tax = 0
        for fee in self.fees.all():
            sub = fee.price * fee.amount
            subtotal += sub
            t_tax += sub * (self.tax / 100)
            t_reverse_tax += sub * (self.reverse_tax / 100)
        total = subtotal + t_tax - t_reverse_tax
        res = []
        res.append(['subtotal', 'Subtotal', subtotal])
        if self.tax:
            name = '{} ({}%)'.format(self.taxname, self.tax)
            res.append(['tax', name, t_tax])
        if self.reverse_tax:
            name = '{} ({}%)'.format(self.reverse_taxname, self.reverse_tax)
            res.append(['reverse-tax', name, t_reverse_tax])
        if self.extra_currency:
            res.append(['total', 'TOTAL ({})'.format(self.currency), total])
            res.append(['extra-total', 'TOTAL ({}) *'.format(self.extra_currency),
                       total * self.currency_exchange])
        else:
            res.append(['total', 'TOTAL', total])
        return res

    @property
    def total(self):
        total = self.get_totals()[-1][2]
        return round(total, 2)

    def number_wadobo(self):
        return '{}/{:03d}'.format(self.year, self.number)

    def __str__(self):
        res = ''
        if self.prefix:
            res += self.prefix + ' - '
        res += str(self.number)
        if self.year:
            res += ' / ' + str(self.year)
        return res
