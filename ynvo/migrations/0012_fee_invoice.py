# Generated by Django 4.2.7 on 2023-12-05 09:57

from django.db import migrations, models
import django.db.models.deletion


def copy_m2m_to_fk(apps, schema_editor):
    Fee = apps.get_model('ynvo', 'Fee')
    for fee in Fee.objects.all():
        invoices = fee.invoice.all()
        if len(invoices) > 1:
            fee.invoice = invoices[0]
            fee.save()
            for invoice in invoices[1:]:
                fee.pk = None
                fee.invoice = invoice
                fee.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ynvo', '0011_project_task_work_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='fee',
            name='invoice',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='ynvo.invoice'),
        ),
        migrations.RunPython(copy_m2m_to_fk),
    ]
