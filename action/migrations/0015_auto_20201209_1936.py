# Generated by Django 3.1.2 on 2020-12-09 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0014_auto_20201130_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='userhome',
            name='favorite_locations',
            field=models.ManyToManyField(blank=True, related_name='favorite_of_user', to='action.Location'),
        ),
        migrations.AddField(
            model_name='userhome',
            name='recent_locations',
            field=models.ManyToManyField(blank=True, related_name='recent_of_user', to='action.Location'),
        ),
        migrations.AlterField(
            model_name='userhome',
            name='organizations',
            field=models.ManyToManyField(blank=True, to='action.Organization'),
        ),
    ]