# Generated by Django 3.2.11 on 2023-01-24 08:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('masters', '0001_initial'),
        ('gtcc', '0001_initial'),
        ('entity', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicerequestlog',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequestlog',
            name='driver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='log_driver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequestlog',
            name='service_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_service_request', to='entity.servicerequest'),
        ),
        migrations.AddField(
            model_name='servicerequestlog',
            name='vehicle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='log_vehicle', to='gtcc.vehicledetail'),
        ),
        migrations.AddField(
            model_name='servicerequestdetailimage',
            name='service_request_detail',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_request_detail', to='entity.servicerequestdetail'),
        ),
        migrations.AddField(
            model_name='servicerequestdetailimage',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_request_image_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequestdetail',
            name='grease_trap',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_request_grease_trap', to='entity.entitygreasetrap'),
        ),
        migrations.AddField(
            model_name='servicerequestdetail',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_detail_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequestdetail',
            name='service_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_request', to='entity.servicerequest'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='driver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_driver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='dumping_vehicledetails',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_dumped_vehicledetails', to='gtcc.vehicleentrydetails'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_request_entity', to='entity.entity'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='entity_gtcc',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_request_entity_gtcc', to='entity.entitygtcc'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='operator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_operator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='vehicle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_request_vehicle', to='gtcc.vehicledetail'),
        ),
        migrations.AddField(
            model_name='entitylog',
            name='action_taken_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entitylog_account', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entitylog',
            name='action_taken_on',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entitylog_entity', to='entity.entity'),
        ),
        migrations.AddField(
            model_name='entitylog',
            name='related_self_log',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entitylog_entitylog', to='entity.entitylog'),
        ),
        migrations.AddField(
            model_name='entitygtcc',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_gtcc_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entitygtcc',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_gtcc_entity', to='entity.entity'),
        ),
        migrations.AddField(
            model_name='entitygtcc',
            name='gtcc',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_gtcc', to='gtcc.gtcc'),
        ),
        migrations.AddField(
            model_name='entitygtcc',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entity_gtcc_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entitygreasetrap',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_grease_trap_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entitygreasetrap',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_grease_trap_entity', to='entity.entity'),
        ),
        migrations.AddField(
            model_name='entitygreasetrap',
            name='grease_trap',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_grease_trap', to='masters.greasetrap'),
        ),
        migrations.AddField(
            model_name='entitygreasetrap',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entity_grease_trap_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entityfixture',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_fixture_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entityfixture',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_fixture_entity', to='entity.entity'),
        ),
        migrations.AddField(
            model_name='entityfixture',
            name='fixture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_fixture', to='masters.fixture'),
        ),
        migrations.AddField(
            model_name='entityfixture',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entity_fixture_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entity',
            name='active_contact_person',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_active_contact_person', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entity',
            name='active_gtcc_detail',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_active_gtcc', to='entity.entitygtcc'),
        ),
        migrations.AddField(
            model_name='entity',
            name='area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_area', to='masters.area'),
        ),
        migrations.AddField(
            model_name='entity',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_category', to='masters.maincategory'),
        ),
        migrations.AddField(
            model_name='entity',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entity',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entity',
            name='sub_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_subcategory', to='masters.subcategory'),
        ),
        migrations.AddField(
            model_name='entity',
            name='subarea',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_subarea', to='masters.subarea'),
        ),
        migrations.AddField(
            model_name='entity',
            name='zone',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_zone', to='masters.zone'),
        ),
    ]
