# Generated by Django 2.1 on 2018-08-09 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alech', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='exportfile',
            name='file',
            field=models.FileField(null=True, upload_to='exports/', verbose_name='Export file'),
        ),
    ]