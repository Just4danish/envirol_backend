# Generated by Django 3.2.11 on 2023-02-24 12:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('masters', '0014_auto_20230224_1641'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entity', '0006_alter_entity_foodwatch_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityGreaseTrapInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capacity', models.DecimalField(decimal_places=2, max_digits=6)),
                ('current_cleaning_frequency', models.IntegerField()),
                ('required_cleaning_frequency', models.IntegerField()),
                ('last_cleaning_date', models.DateField()),
                ('inspection_status', models.CharField(choices=[('Completed', 'Completed'), ('Pending', 'Pending'), ('Skipped', 'Skipped'), ('Reinspection', 'Reinspection')], default='Pending', max_length=15)),
                ('grease_trap_condtion', models.CharField(choices=[('Perfect', 'Perfect'), ('Good', 'Good'), ('Old', 'Old'), ('Damaged', 'Damaged'), ('Unavailable', 'Unavailable'), ('Not set', 'Not set')], default='Not set', max_length=20)),
                ('cover_condition', models.CharField(choices=[('Perfect', 'Perfect'), ('Good', 'Good'), ('Old', 'Old'), ('Damaged', 'Damaged'), ('Unavailable', 'Unavailable'), ('Not set', 'Not set')], default='Not set', max_length=20)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_grease_trap_created_by', to=settings.AUTH_USER_MODEL)),
                ('entity_grease_trap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_grease_trap', to='entity.entitygreasetrap')),
            ],
        ),
        migrations.CreateModel(
            name='EntityInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inspection_id', models.CharField(max_length=100)),
                ('establishment_name', models.CharField(max_length=255)),
                ('makhani_no', models.CharField(blank=True, max_length=100, null=True)),
                ('trade_license_no', models.CharField(blank=True, max_length=100, null=True)),
                ('entity_location', models.CharField(blank=True, max_length=255, null=True)),
                ('phone_no', models.CharField(blank=True, max_length=50, null=True)),
                ('meals_per_day', models.DecimalField(decimal_places=2, max_digits=6, null=True)),
                ('seating_capacity', models.DecimalField(decimal_places=2, max_digits=6, null=True)),
                ('remarks', models.TextField(null=True)),
                ('is_inspection_follow_up', models.BooleanField()),
                ('is_report_to_dm', models.BooleanField()),
                ('inspection_status', models.CharField(choices=[('Completed', 'Completed'), ('Pending', 'Pending')], default='Pending', max_length=10)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')], default='Active', max_length=20)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inspection_entity_area', to='masters.area')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_created_by', to=settings.AUTH_USER_MODEL)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity', to='entity.entity')),
                ('modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EntityInspectionImages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='')),
                ('image_type', models.CharField(max_length=10)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('entity_inspection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_image_entity', to='inspector.entityinspection')),
            ],
        ),
        migrations.CreateModel(
            name='EntityGreaseTrapInspectionImages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='')),
                ('image_type', models.CharField(choices=[('Before', 'Before'), ('After', 'After')], max_length=10)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('entity_grease_trap_inspection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_grease_trap_inspection_image', to='inspector.entitygreasetrapinspection')),
            ],
        ),
        migrations.AddField(
            model_name='entitygreasetrapinspection',
            name='entity_inspection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_detail', to='inspector.entityinspection'),
        ),
        migrations.AddField(
            model_name='entitygreasetrapinspection',
            name='grease_trap',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_grease_trap', to='masters.greasetrap'),
        ),
        migrations.AddField(
            model_name='entitygreasetrapinspection',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inspection_entity_grease_trap_modified_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
