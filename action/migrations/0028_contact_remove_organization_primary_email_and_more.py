# Generated by Django 4.1.7 on 2023-12-12 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0027_alter_organizationcontact_contacttype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contacttype', models.CharField(choices=[('OTHR', 'Other Contact Adress'), ('MAIL', 'Email Adress'), ('PHON', 'Phone Number'), ('WEBS', 'Organization Website URL'), ('TWTR', 'X (formerly twitter) URL'), ('FCBK', 'Facebook URL'), ('INSG', 'Instagram URL')], default='OTHR', max_length=4)),
                ('adress', models.CharField(max_length=200)),
                ('info', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='organization',
            name='primary_email',
        ),
        migrations.AddField(
            model_name='organization',
            name='contacts',
            field=models.ManyToManyField(blank=True, to='action.contact'),
        ),
    ]
