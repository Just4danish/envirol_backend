# Generated by Django 3.2.11 on 2023-02-16 12:57

from django.db import migrations, models
import gtcc.models


class Migration(migrations.Migration):

    dependencies = [
        ('gtcc', '0006_auto_20230216_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicleentrydetails',
            name='job_log',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='status',
            field=models.CharField(choices=[('Issued', 'Issued'), ('Scanned', 'Scanned'), ('Used', 'Used'), ('Converted', 'Converted'), ('Lost', 'Lost')], default='Issued', max_length=20),
        ),
        migrations.AlterField(
            model_name='gtcc',
            name='image',
            field=models.ImageField(null=True, upload_to=gtcc.models.content_file_name),
        ),
    ]
