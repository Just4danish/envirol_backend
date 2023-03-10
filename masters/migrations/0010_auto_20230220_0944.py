# Generated by Django 3.2.11 on 2023-02-20 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0009_alter_gate_gate_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='gate',
            name='gate_status',
            field=models.CharField(choices=[('Active', 'Active'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')], default='Closed', max_length=10),
        ),
        migrations.AlterField(
            model_name='gate',
            name='gate_id',
            field=models.CharField(default='2PdxB0OSSQDWc7oIyGm4qv0RmbpwKJwH', editable=False, max_length=32, unique=True),
        ),
    ]
