# Generated by Django 3.1.1 on 2022-10-17 17:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0023_auto_20210610_1443'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gmaps_Locations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('place_id', models.CharField(max_length=30)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='action.location')),
            ],
        ),
        migrations.CreateModel(
            name='Gmaps_LookupString',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lookup_string', models.CharField(max_length=100)),
                ('Gmaps_Location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='action.gmaps_locations')),
            ],
        ),
    ]