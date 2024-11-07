# Generated by Django 5.1.2 on 2024-11-01 17:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tribe', '0003_rename_sensitiveinfo_contactinfo_hood'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contactinfo',
            old_name='secret',
            new_name='info',
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='in_revent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tribe.revent'),
        ),
    ]
