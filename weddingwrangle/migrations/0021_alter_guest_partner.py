# Generated by Django 4.0.7 on 2023-07-13 10:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weddingwrangle', '0020_email_date_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guest',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='weddingwrangle.guest'),
        ),
    ]
