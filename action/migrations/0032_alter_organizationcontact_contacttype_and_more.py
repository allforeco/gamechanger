# Generated by Django 4.1.7 on 2023-12-20 14:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0031_remove_organization_primary_location_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationcontact',
            name='contacttype',
            field=models.CharField(choices=[('OTHR', 'Other Contact Adress'), ('MAIL', 'Email Adress'), ('PHON', 'Phone Number'), ('WEBS', 'Organization Website URL'), ('YOUT', 'Youtube URL'), ('TWTR', 'X (formerly twitter) URL'), ('FCBK', 'Facebook URL'), ('INSG', 'Instagram URL')], default='OTHR', max_length=4),
        ),
        migrations.AlterField(
            model_name='organizationcontact',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='action.organization'),
        ),
    ]
