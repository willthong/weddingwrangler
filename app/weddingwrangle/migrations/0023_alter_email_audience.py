# Generated by Django 4.2.7 on 2025-01-30 19:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("weddingwrangle", "0022_main_starter_guest_main_guest_starter"),
    ]

    operations = [
        migrations.AlterField(
            model_name="email",
            name="audience",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="email",
                to="weddingwrangle.audience",
            ),
        ),
    ]
