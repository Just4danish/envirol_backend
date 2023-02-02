# Generated by Django 3.2.11 on 2023-01-25 11:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gtcc', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicleentrydetails',
            name='operator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='accesscontrollog',
            name='status',
            field=models.CharField(choices=[('Entered', 'Entered'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Discharged', 'Discharged'), ('Exited', 'Exited')], max_length=10, null=True),
        ),
    ]