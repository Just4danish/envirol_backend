# Generated by Django 3.2.11 on 2023-01-31 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodwatch', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodwatchentity',
            name='business_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
