# Generated by Django 4.1.7 on 2023-12-21 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0035_rename_adress_organizationcontact_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationcontact',
            name='category',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='organizationcontact',
            name='contacttype',
            field=models.CharField(choices=[('OTHR', 'Other Contact Address'), ('MAIL', 'Email Address'), ('PHON', 'Phone Number'), ('WEBS', 'Organization Website URL'), ('YOUT', 'Youtube URL'), ('TWTR', 'X (formerly twitter) URL'), ('FCBK', 'Facebook URL'), ('INSG', 'Instagram URL')], default='OTHR', max_length=4),
        ),
    ]