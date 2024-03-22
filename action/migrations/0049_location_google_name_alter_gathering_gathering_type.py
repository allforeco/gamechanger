# Generated by Django 4.1.7 on 2024-03-01 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0048_remove_country_location_location_in_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='google_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='gathering',
            name='gathering_type',
            field=models.CharField(choices=[('STRK', 'Strike'), ('DEMO', 'Demonstration'), ('NVDA', 'Non-Violent Direct Action'), ('MEET', 'Meetup'), ('CIRC', 'Circle (MothersRebellion)'), ('OTHR', 'Other')], default='STRK', max_length=4),
        ),
    ]
