# Generated by Django 4.1.7 on 2023-03-26 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('klapp', '0003_alter_actor_conversation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='created_by',
            field=models.ForeignKey(blank=True, editable=False, on_delete=django.db.models.deletion.PROTECT, to='klapp.actor'),
        ),
        migrations.AlterField(
            model_name='post',
            name='media_url',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='settings',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
    ]