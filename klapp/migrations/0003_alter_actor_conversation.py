# Generated by Django 4.1.7 on 2023-03-26 07:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('klapp', '0002_alter_actor_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actor',
            name='conversation',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='klapp.conversation'),
        ),
    ]