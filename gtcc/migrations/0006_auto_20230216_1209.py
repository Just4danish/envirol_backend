# Generated by Django 3.2.11 on 2023-02-16 08:09

from django.db import migrations, models
import gtcc.models


class Migration(migrations.Migration):

    dependencies = [
        ('gtcc', '0005_gtcc_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gtcc',
            name='image',
            field=models.ImageField(null=True, upload_to=gtcc.models.content_file_name),
        ),
        migrations.AlterField(
            model_name='gtcc',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Approval Pending', 'Approval Pending'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted'), ('Rejected', 'Rejected')], default='Active', max_length=20),
        ),
        migrations.AlterField(
            model_name='vehicledetail',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Approval Pending', 'Approval Pending'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted'), ('Rejected', 'Rejected')], default='Active', max_length=20),
        ),
    ]