# Generated by Django 4.1.7 on 2023-12-20 14:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0032_alter_organizationcontact_contacttype_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationcontact',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='action.location'),
        ),
    ]
