# Generated by Django 3.2.11 on 2023-02-15 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gtcc', '0003_auto_20230125_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesscontrollog',
            name='status',
            field=models.CharField(choices=[('Entered', 'Entered'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Discharged', 'Discharged'), ('Exited', 'Exited')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='booklet',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Issued', 'Issued'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')], default='Active', max_length=20),
        ),
        migrations.AlterField(
            model_name='checkoutdetail',
            name='status',
            field=models.CharField(choices=[('Initiated', 'Initiated'), ('Success', 'Success'), ('Failed', 'Failed')], default='Initiated', max_length=20),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='status',
            field=models.CharField(choices=[('Issued', 'Issued'), ('Used', 'Used'), ('Converted', 'Converted'), ('Lost', 'Lost')], default='Issued', max_length=20),
        ),
        migrations.AlterField(
            model_name='couponbooklet',
            name='status',
            field=models.CharField(choices=[('Issued', 'Issued'), ('In Use', 'In Use'), ('Used', 'Used')], default='Issued', max_length=20),
        ),
        migrations.AlterField(
            model_name='gtcc',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Approval Pending', 'Approval Pending'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')], default='Active', max_length=20),
        ),
        migrations.AlterField(
            model_name='vehicledetail',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Approval Pending', 'Approval Pending'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')], default='Active', max_length=20),
        ),
    ]