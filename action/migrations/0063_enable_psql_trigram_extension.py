# Generated by Django 5.1.2 on 2025-03-09 09:44
# by janl using the command 
# python manage.py makemigrations --empty action

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):

    dependencies = [
        ('action', '0062_alter_gathering_coordinator_alter_gathering_guide_and_more'),
    ]

    operations = [
        TrigramExtension()
    ]
