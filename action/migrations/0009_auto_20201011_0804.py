# Generated by Django 3.1.2 on 2020-10-11 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0008_gathering_belong'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gathering_witness',
            old_name='creation_date',
            new_name='creation_time',
        ),
        migrations.RemoveField(
            model_name='gathering',
            name='end_date_time',
        ),
        migrations.RemoveField(
            model_name='gathering',
            name='start_date_time',
        ),
        migrations.AddField(
            model_name='gathering',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gathering',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gathering_witness',
            name='updated',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
