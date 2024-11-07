# Generated by Django 5.1.2 on 2024-11-01 17:25

import django.db.models.deletion
import tribe.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tribe', '0002_rename_group_revent_rename_groupnote_reventnote_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SensitiveInfo',
            new_name='ContactInfo',
        ),
        migrations.CreateModel(
            name='Hood',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('pubkey', tribe.models.Key()),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tribe.person')),
            ],
        ),
    ]
