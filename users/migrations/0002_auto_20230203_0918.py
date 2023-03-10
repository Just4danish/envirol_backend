# Generated by Django 3.2.11 on 2023-02-03 05:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gtcc', '0003_auto_20230125_1523'),
        ('masters', '0003_auto_20230130_1633'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='assigned_vehicle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_vehicle', to='gtcc.vehicledetail'),
        ),
        migrations.AlterField(
            model_name='account',
            name='designation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_designation', to='masters.designation'),
        ),
        migrations.AlterField(
            model_name='account',
            name='inviter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inviter_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='account',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='account_modified_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
