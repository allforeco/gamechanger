# Generated by Django 4.1.7 on 2024-04-24 11:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0052_remove_location_verified_location_creation_details_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location_Belong',
            fields=[
                ('duplicate', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.PROTECT, primary_key=True, serialize=False, to='action.location')),
                ('prime', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='action.location')),
            ],
        ),
    ]
