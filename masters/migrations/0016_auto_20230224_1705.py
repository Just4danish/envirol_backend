# Generated by Django 3.2.11 on 2023-02-24 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0015_auto_20230224_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='gate',
            name='last_query_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='gate',
            name='remote',
            field=models.CharField(choices=[('Online', 'Online'), ('Offline', 'Offline')], default='Offline', max_length=10),
        ),
        migrations.AlterField(
            model_name='gate',
            name='gate_id',
            field=models.CharField(default='kitZ7hS16aUkpCK98WtuDSJuhcba79tC', editable=False, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='gate',
            name='gate_status',
            field=models.CharField(choices=[('Open', 'Open'), ('Closed', 'Closed')], default='Closed', max_length=10),
        ),
    ]
