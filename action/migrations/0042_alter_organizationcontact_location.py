# Generated by Django 4.1.7 on 2024-01-08 14:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0041_alter_organizationcontact_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationcontact',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='action.location'),
        ),
    ]
