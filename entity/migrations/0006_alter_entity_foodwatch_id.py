# Generated by Django 3.2.11 on 2023-02-23 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0005_entitygreasetrap_foodwatch_grease_trap_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='foodwatch_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]