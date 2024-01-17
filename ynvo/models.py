from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from ynvo.choices import TaskStatus
from ynvo.managers import (
    ReadClientManager,
    ReadCommentManager,
    ReadProjectManager,
    ReadTaskManager,
    ReadWorkManager,
    WriteClientManager,
    WriteCommentManager,
    WriteProjectManager,
    WriteTaskManager,
    WriteWorkManager,
)


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
    transmitter = models.ForeignKey(
        "ynvo.Transmitter", related_name="clients", on_delete=models.PROTECT, null=True
    )

    objects = WriteClientManager()
    read_objects = ReadClientManager()

    def __str__(self):
        return self.alias


class Transmitter(PersonalData):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    payment = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    INVO_STATUS = (
        ("created", "created"),
        ("send", "send"),
        ("received", "received"),
    )

    prefix = models.CharField(max_length=32, blank=True, null=True)
    number = models.PositiveIntegerField(blank=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    invo_from = models.ForeignKey(Transmitter, on_delete=models.PROTECT)
    invo_to = models.ForeignKey(Client, on_delete=models.PROTECT)
    project = models.CharField(max_length=128, default="", blank=True)
    currency = models.CharField(max_length=4, default="€")
    extra_currency = models.CharField(max_length=4, blank=True, null=True)
    currency_exchange = models.FloatField(default=1.0)
    tax = models.IntegerField(default=21)
    taxname = models.CharField(max_length=16, default="IVA")
    reverse_tax = models.IntegerField(default=15)
    reverse_taxname = models.CharField(max_length=16, default="IRPF")
    note = models.TextField(blank=True, null=True)
    created = models.DateField(editable=True, blank=True)
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
        res.append(["subtotal", "Subtotal", subtotal])
        if self.tax:
            name = "{} ({}%)".format(self.taxname, self.tax)
            res.append(["tax", name, t_tax])
        if self.reverse_tax:
            name = "{} ({}%)".format(self.reverse_taxname, self.reverse_tax)
            res.append(["reverse-tax", name, t_reverse_tax])
        if self.extra_currency:
            res.append(["total", "TOTAL ({})".format(self.currency), total])
            res.append(
                [
                    "extra-total",
                    "TOTAL ({}) *".format(self.extra_currency),
                    total * self.currency_exchange,
                ]
            )
        else:
            res.append(["total", "TOTAL", total])
        return res

    @property
    def total(self):
        total = self.get_totals()[-1][2]
        return round(total, 2)

    def number_wadobo(self):
        return "{}/{:03d}".format(self.year, self.number)

    def save(self, *args, **kwargs):
        if not self.id:
            now = timezone.now()
            self.created = now
            self.year = now.year
            if not self.number:
                try:
                    last_number = (
                        Invoice.objects.filter(year=self.year)
                        .order_by("-number")
                        .values_list("number", flat=True)[0]
                    ) or 0
                except Exception:
                    last_number = 0
                self.number = last_number + 1
        return super().save(*args, **kwargs)

    def __str__(self):
        res = ""
        if self.prefix:
            res += self.prefix + " - "
        res += str(self.number)
        if self.year:
            res += " / " + str(self.year)
        return res

    class Meta:
        ordering = ("-number",)


class Fee(models.Model):
    FEE_TYPES = (
        ("hour", "hour"),
        ("unit", "unit"),
        ("total", "total"),
    )

    invoice = models.ForeignKey(Invoice, related_name="fees", on_delete=models.PROTECT)
    ftype = models.CharField(max_length=8, choices=FEE_TYPES, default="hour")
    activity = models.CharField(max_length=256)
    price = models.FloatField()
    amount = models.IntegerField(default=1)

    def __str__(self):
        return "{}: {} x {}".format(self.ftype, self.price, self.amount)


class Project(models.Model):
    client = models.ForeignKey(
        Client, related_name="projects", on_delete=models.PROTECT
    )
    name = models.CharField(max_length=128)
    price_per_hour = models.FloatField()
    discount = models.FloatField()

    objects = WriteProjectManager()
    read_objects = ReadProjectManager()

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def __str__(self):
        return self.name


class Task(models.Model):
    project = models.ForeignKey(Project, related_name="tasks", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    priority = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    status = models.CharField(
        max_length=128, choices=TaskStatus.choices, default=TaskStatus.PENDING
    )
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(default=None, blank=True, null=True)
    branch = models.CharField(max_length=128, blank=True, null=True)

    objects = WriteTaskManager()
    read_objects = ReadTaskManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"


class Comment(models.Model):
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(Task, related_name="comments", on_delete=models.CASCADE)

    objects = WriteCommentManager()
    read_objects = ReadCommentManager()

    def __str__(self):
        return self.comment.strip()[:50]

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"


class Work(models.Model):
    amount = models.FloatField()
    work_type = models.CharField(
        max_length=8, choices=(("hour", "hour"), ("total", "total"))
    )
    comment = models.TextField()
    date = models.DateField()
    task = models.ForeignKey(Task, related_name="works", on_delete=models.CASCADE)

    objects = WriteWorkManager()
    read_objects = ReadWorkManager()

    def __str__(self):
        return f"{self.task.name} - {self.comment}"

    class Meta:
        verbose_name = "Trabajo"
        verbose_name_plural = "Trabajos"
