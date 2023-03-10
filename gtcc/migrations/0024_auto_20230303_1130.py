# Generated by Django 3.2.11 on 2023-03-03 07:30

from django.db import migrations, models
import gtcc.models


class Migration(migrations.Migration):

    dependencies = [
        ('gtcc', '0023_alter_gtcc_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicleentrydetails',
            name='delivery_order_file',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='gtcc',
            name='image',
            field=models.ImageField(null=True, upload_to=gtcc.models.content_file_name),
        ),
    ]
