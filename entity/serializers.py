from rest_framework import serializers
from .models import *
from users.models import Account
from users.serializers import UserLimitedDetailSerializer
from masters.serializers import SubCategoryListSerializer, SubAreaListSerializer, FixtureListSerializer, GreaseTrapListSerializer, Designation
from gtcc.serializers import GTCCListSerializer, GTCCLimitedDetailsListSerializer, VehicleLimitedListSerializer, GTCCDropdownListSerializer, VehicleEntryDetailsLimitedSerializer
from abacimodules.abacifunctions import name_maker
from django.utils.crypto import get_random_string
from django.utils import timezone
import datetime

common_exclude_list = ['created_by', 'modified_by']


class EntityPostSerializer(serializers.ModelSerializer):
    contact_person =  serializers.CharField()
    contact_number =  serializers.CharField(allow_null=True)
    email =  serializers.EmailField()
    emirate =  serializers.CharField(allow_null=True)
    designation =  serializers.IntegerField(allow_null=True)

    def create(self, validated_data):
        contact_person = validated_data.pop("contact_person")
        contact_number = validated_data.pop("contact_number")
        email = validated_data.pop("email")
        emirate = validated_data.pop("emirate")
        designation = validated_data.pop("designation")
        check_email = Account.objects.filter(email=email).first()
        if check_email:
             raise serializers.ValidationError("User with this email id already exist")
        if designation is not None:
            designation = Designation.objects.get(pk=designation)
        entity = Entity.objects.create(**validated_data, random_key = get_random_string(64).lower())
        first_name, last_name = name_maker(contact_person)
        active_contact_person = Account.objects.create(
                inviter             =   validated_data.get('created_by'),
                email               =   email,
                username            =   email,
                first_name          =   first_name,
                last_name           =   last_name,
                emirate             =   emirate,
                designation         =   designation,
                contact_number      =   contact_number,
                link_id             =   entity.id,
                link_class          =   'Entity',
                user_class          =   'Entity',
                user_type           =   'User',
                inviting_key        =   get_random_string(64).lower(),
                invited_date        =   timezone.now(),
                invite_expiry_date  =   (timezone.now() + datetime.timedelta(3)),)
        active_contact_person.send_invitation()
        entity.active_contact_person = active_contact_person
        entity.save()
        return entity

    def update(self, instance, validated_data):
        user = instance.active_contact_person
        contact_person = validated_data.get('contact_person')
        contact_number = validated_data.get("contact_number")
        email = validated_data.get("email")
        emirate = validated_data.get("emirate")
        designation = validated_data.get("designation")
        check_email = Account.objects.filter(email=email).exclude(pk=user.id).first()
        if check_email:
             raise serializers.ValidationError("User with this email id already exist")
        if designation is not None:
            designation = Designation.objects.get(pk=designation)
        instance.establishment_name = validated_data.get('establishment_name')
        instance.trade_license_no = validated_data.get('trade_license_no')
        instance.trade_license_name = validated_data.get('trade_license_name')
        instance.env_sap_id = validated_data.get('env_sap_id')
        instance.foodwatch_id = validated_data.get('foodwatch_id')
        instance.foodwatch_business_id = validated_data.get('foodwatch_business_id')
        instance.job_card_no = validated_data.get('job_card_no')
        instance.category = validated_data.get('category')
        instance.sub_category = validated_data.get('sub_category')
        instance.zone = validated_data.get('zone')
        instance.area = validated_data.get('area')
        instance.subarea = validated_data.get('subarea')
        instance.address = validated_data.get('address')
        instance.phone_no = validated_data.get('phone_no')
        instance.entity_location = validated_data.get('entity_location')
        instance.location_remark = validated_data.get('location_remark')
        instance.po_box = validated_data.get('po_box')
        instance.seating_capacity = validated_data.get('seating_capacity')
        instance.gps_coordinates = validated_data.get('gps_coordinates')
        instance.google_location = validated_data.get('google_location')
        instance.makhani_no = validated_data.get('makhani_no')
        instance.meals_per_day = validated_data.get('meals_per_day')
        instance.modified_by = validated_data.get('modified_by')
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        first_name, last_name = name_maker(contact_person)
        if email == user.email:
            user.first_name          =   first_name
            user.last_name           =   last_name
            user.emirate             =   emirate
            user.designation         =   designation
            user.contact_number      =   contact_number
            user.modified_by         =   validated_data.get('modified_by')
            user.save()
        else:
            if user.user_status == 'Invited':
                user.first_name          =   first_name
                user.last_name           =   last_name
                user.emirate             =   emirate
                user.username            =   email
                user.email               =   email
                user.designation         =   designation
                user.contact_number      =   contact_number
                user.inviting_key        =   get_random_string(64).lower()
                user.invited_date        =   timezone.now()
                user.invite_expiry_date  =   timezone.now() + datetime.timedelta(3)
                user.modified_by         =   validated_data.get('modified_by')
                user.save()
                user.send_invitation()
            else:
                user.user_status         =   'Deactivated'
                user.modified_by         =   validated_data.get('modified_by')
                user.save()   
                active_contact_person = Account.objects.create(
                            inviter             =   validated_data.get('modified_by'),
                            email               =   email,
                            username            =   email,
                            first_name          =   first_name,
                            last_name           =   last_name,
                            emirate             =   emirate,
                            designation         =   designation,
                            contact_number      =   contact_number,
                            link_id             =   instance.id,
                            link_class          =   'Entity',
                            user_class          =   'Entity',
                            user_type           =   'User',
                            inviting_key        =   get_random_string(64).lower(),
                            invited_date        =   timezone.now(),
                            invite_expiry_date  =   (timezone.now() + datetime.timedelta(3)),)
                active_contact_person.send_invitation()
                instance.active_contact_person = active_contact_person
                instance.save()
        return instance
             
    class Meta:
        model = Entity
        exclude = ['zone', 'area', 'category', 'random_key', 'created_by']

class EntityFixturePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityFixture
        exclude = ['created_by']

class EntityFixtureListSerializer(serializers.ModelSerializer):
    fixture = FixtureListSerializer()
    class Meta:
        model = EntityFixture
        exclude = common_exclude_list

class EntityGreaseTrapPostSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['last_cleaning_date'] > timezone.now().date():
            raise serializers.ValidationError("Future date not allowed for last cleaning date")
        return data

    class Meta:
        model = EntityGreaseTrap
        exclude = ['grease_trap_label', 'next_cleaning_date', 'created_by']

class EntityGreaseTrapListSerializer(serializers.ModelSerializer):
    grease_trap = GreaseTrapListSerializer()
    class Meta:
        model = EntityGreaseTrap
        exclude = common_exclude_list

class EntityGTCCPostSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        entity = validated_data.get('entity')
        check_active_gtcc = EntityGTCC.objects.filter(entity=entity).exclude(status='Rejected').exclude(status='Expired').last()
        if check_active_gtcc:
            if check_active_gtcc.status == 'Approval Pending':
                raise serializers.ValidationError("You have one approval pending contract")
            check_active_gtcc.status = 'Expired'
            check_active_gtcc.contract_end = datetime.date.today()
            check_active_gtcc.save()
        active_gtcc_detail = EntityGTCC.objects.create(**validated_data)
        entity.active_gtcc_detail = active_gtcc_detail
        entity.modified_by = validated_data.get('created_by')
        entity.save()
        return active_gtcc_detail

    class Meta:
        model = EntityGTCC
        exclude = ['created_by']

class EntityGTCCListSerializer(serializers.ModelSerializer):
    gtcc = GTCCListSerializer()
    class Meta:
        model = EntityGTCC
        exclude = common_exclude_list

class EntityGTCCLimitedListSerializer(serializers.ModelSerializer):
    gtcc = GTCCLimitedDetailsListSerializer()
    class Meta:
        model = EntityGTCC
        exclude = common_exclude_list

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        exclude = common_exclude_list

class EntityListSerializer(serializers.ModelSerializer):
    active_contact_person = UserLimitedDetailSerializer()
    sub_category = SubCategoryListSerializer()
    subarea = SubAreaListSerializer()
    entity_fixture_entity = EntityFixtureListSerializer(many=True)
    entity_grease_trap_entity = EntityGreaseTrapListSerializer(many=True)
    entity_gtcc_entity = EntityGTCCListSerializer(many=True)
    class Meta:
        model = Entity
        exclude = ['category','zone','area','created_by', 'created_date', 'modified_by', 'modified_date']

class EntityLimitedListSerializer(serializers.ModelSerializer):
    subarea = SubAreaListSerializer()
    sub_category = SubCategoryListSerializer()
    active_gtcc_detail = EntityGTCCLimitedListSerializer()
    class Meta:
        model = Entity
        fields = ['id', 'establishment_name', 'address', 'subarea', 'sub_category', 'status', 'random_key', 'active_gtcc_detail']

class EntityWithGreaseTrapsSerializer(serializers.ModelSerializer):
    entity_grease_trap_entity = EntityGreaseTrapListSerializer(many=True)
    class Meta:
        model = Entity
        fields = ['id', 'establishment_name', 'entity_grease_trap_entity']

class GTCCContractListSerializer(serializers.ModelSerializer):
    entity = EntityLimitedListSerializer()
    gtcc = GTCCDropdownListSerializer()
    class Meta:
        model = EntityGTCC
        exclude = common_exclude_list

class EntityGreaseTrapDetailedSerializer(serializers.ModelSerializer):
    entity = EntityLimitedListSerializer()
    grease_trap = GreaseTrapListSerializer()
    class Meta:
        model = EntityGreaseTrap
        exclude = common_exclude_list

# class EntityQRCodeScanSerializer(serializers.Serializer):
#     random_key = serializers.CharField()
#     service_request_id = serializers.IntegerField(required=False)

#     def create(self, validated_data):
#         random_key      = validated_data.get('random_key')
#         service_request = validated_data.get('service_request_id', None)
#         driver          = validated_data.get('driver')
#         entity_data     = Entity.objects.filter(random_key=random_key).exclude(status='Deleted').first()
#         if not entity_data:
#             raise serializers.ValidationError('Entity not found')
#         if service_request == None:
#             data = ServiceRequest.objects.filter(entity=entity_data)
#             return ServiceRequestListSerializer(data, many=True).data
#         else:
#             try:
#                 service_request_data = ServiceRequest.objects.get(pk=service_request, status='Assigned')
#             except ServiceRequest.DoesNotExist:
#                 raise serializers.ValidationError("Service request not found")
#             if service_request_data.entity != entity_data:
#                 raise serializers.ValidationError("This service request could not be associated with the scanned entity")
#             elif service_request_data.driver != driver:
#                 raise serializers.ValidationError("This service request not associated with you")
#             else:
#                 service_request_data.status = 'Processing'
#                 service_request_data.save()
#                 ServiceRequestLog.objects.create(
#                     service_request = service_request_data,
#                     vehicle = service_request_data.vehicle,
#                     driver = driver,
#                     type = "Job Started",
#                     log = f"This job has been started by Mr.{driver.full_name} at the {entity_data.establishment_name} restaurant",
#                     created_by = driver
#                 )
#                 return ServiceRequestListSerializer(service_request_data).data

class ServiceRequestPostSerializer(serializers.ModelSerializer):
    grease_traps =  serializers.ListField()
    sr_grease_trap_status = serializers.CharField(default='Pending')

    class Meta:
        model = ServiceRequest
        exclude = ['entity_gtcc', 'grease_trap_count']

    def create(self, validated_data):
        grease_traps              = validated_data.pop("grease_traps")
        sr_grease_trap_status     = validated_data.pop("sr_grease_trap_status")
        entity                    = validated_data.get("entity")
        created_by                = validated_data.get("created_by")
        active_gtcc_detail        = entity.active_gtcc_detail
        establishment_name        = entity.establishment_name
        if active_gtcc_detail == None:
            raise serializers.ValidationError("There is no GTCC assigned for this entity")
        
        if active_gtcc_detail.status == 'Active':
            sr_list = []
            for grease_trap in grease_traps:
                service_request = ServiceRequest.objects.create(**validated_data, entity_gtcc = active_gtcc_detail, grease_trap_count = 1)
                driver          = service_request.driver
                grease_trap_data = EntityGreaseTrap.objects.get(pk=grease_trap)
                ServiceRequestDetail.objects.create(
                    service_request = service_request,
                    grease_trap = grease_trap_data,
                    status = sr_grease_trap_status
                )
                ServiceRequestLog.objects.create(
                    service_request = service_request,
                    type = "Initiated",
                    log = "Job initiated from "+establishment_name,
                    created_by = created_by
                )
                if sr_grease_trap_status == 'Completed':
                    ServiceRequestLog.objects.create(
                        service_request = service_request,
                        vehicle = service_request.vehicle,
                        driver = driver,
                        type = "Job Completed",
                        log = f"This job has been completed by Mr.{driver.full_name} at the {entity.establishment_name} restaurant",
                        created_by = created_by
                    )
                sr_list.append(service_request)
            return sr_list
        else:
            raise serializers.ValidationError("There is no active GTCC exist for this entity")

class ServiceRequestImageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestDetailImage
        fields = ['id', 'image', 'image_type']
        
class ServiceRequestDetailListSerializer(serializers.ModelSerializer):
    grease_trap = EntityGreaseTrapListSerializer()
    service_request_detail = ServiceRequestImageListSerializer(many = True)
    class Meta:
        model = ServiceRequestDetail
        exclude = ['service_request', 'modified_by', 'modified_date']

class ServiceRequestListSerializer(serializers.ModelSerializer):
    entity = EntityLimitedListSerializer()
    entity_gtcc = EntityGTCCLimitedListSerializer()
    vehicle = VehicleLimitedListSerializer()
    driver = UserLimitedDetailSerializer()
    dumping_vehicledetails = VehicleEntryDetailsLimitedSerializer()
    service_request = ServiceRequestDetailListSerializer(many = True)
    class Meta:
        model = ServiceRequest
        exclude = ['created_by', 'modified_by']

class ServiceRequestSerializer(serializers.ModelSerializer):
    entity = EntityLimitedListSerializer()
    class Meta:
        model = ServiceRequest
        fields = '__all__'

class ServiceRequestLogSerializer(serializers.ModelSerializer):
    vehicle = VehicleLimitedListSerializer()
    driver = UserLimitedDetailSerializer()
    created_by = UserLimitedDetailSerializer()
    class Meta:
        model = ServiceRequestLog
        exclude = ['service_request']
