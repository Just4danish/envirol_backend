# Generated by Django 3.2.11 on 2023-01-31 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodwatch', '0009_auto_20230131_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='foodwatchentity',
            name='is_convertable',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='foodwatchentity',
            name='foodwatch_id',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='foodwatchentity',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Synced', 'Synced'), ('Converted', 'Converted'), ('Deleted', 'Deleted')], default='Pending', max_length=10),
        ),
    ]
