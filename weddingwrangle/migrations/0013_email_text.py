# Generated by Django 4.0.7 on 2023-07-06 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weddingwrangle', '0012_alter_guest_rsvp_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='text',
            field=models.CharField(blank=True, max_length=10000000, null=True),
        ),
    ]
