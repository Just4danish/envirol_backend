# Generated by Django 3.2.11 on 2023-02-22 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0004_auto_20230208_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='entitygreasetrap',
            name='foodwatch_grease_trap_id',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
