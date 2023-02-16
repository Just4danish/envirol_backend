from rest_framework import serializers
from entity.models import ServiceRequest, ServiceRequestLog
from masters.models import RFIDCard, Designation
from .models import *
from users.models import Account
from users.serializers import UserLimitedDetailSerializer
from masters.serializers import ModeOfPaymentListSerializer, RFIDCardLimitedListSerializer
from abacimodules.abacifunctions import name_maker
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import datetime

common_exclude_list = ['created_by', 'created_date', 'modified_by', 'modified_date']

class GTCCPostSerializer(serializers.ModelSerializer):
    contact_person =  serializers.CharField()
    contact_number =  serializers.CharField()
    email =  serializers.EmailField()
    emirate =  serializers.CharField()
    designation =  serializers.IntegerField()

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
        gtcc = GTCC.objects.create(**validated_data)
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
                link_id             =   gtcc.id,
                link_class          =   'GTCC',
                user_class          =   'GTCC',
                user_type           =   'User',
                inviting_key        =   get_random_string(64).lower(),
                invite_expiry_date  =   (timezone.now() + datetime.timedelta(3)),)
        active_contact_person.send_invitation()
        gtcc.active_contact_person = active_contact_person
        gtcc.save()
        return gtcc

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
        instance.address = validated_data.get('address')
        instance.phone_no = validated_data.get('phone_no')
        instance.location = validated_data.get('location')
        instance.location_remark = validated_data.get('location_remark')
        instance.po_box = validated_data.get('po_box')
        instance.website_url = validated_data.get('website_url')
        instance.office_email = validated_data.get('office_email')
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
                user.user_status         =   'Deleted'
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
                        link_class          =   'GTCC',
                        user_class          =   'GTCC',
                        user_type           =   'User',
                        inviting_key        =   get_random_string(64).lower(),
                        invite_expiry_date  =   (timezone.now() + datetime.timedelta(3)),)
            active_contact_person.send_invitation()
            instance.active_contact_person = active_contact_person
            instance.save()
        return instance
             
    class Meta:
        model = GTCC
        exclude = ['created_by']

class GTCCListSerializer(serializers.ModelSerializer):
    active_contact_person = UserLimitedDetailSerializer()
    class Meta:
        model = GTCC
        exclude = common_exclude_list

class GTCCLimitedDetailsListSerializer(serializers.ModelSerializer):
    active_contact_person = UserLimitedDetailSerializer()
    class Meta:
        model = GTCC
        fields = ['id', 'establishment_name', 'status', 'active_contact_person']

class GTCCModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GTCC
        exclude = common_exclude_list

class GTCCDropdownListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GTCC
        fields = ['id', 'establishment_name']

class PaymentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDetail
        exclude = ['previous_balance', 'new_balance', 'created_by']

    def create(self, validated_data):
        gtcc = validated_data.get("gtcc")
        amount = validated_data.get("amount")
        credit_available = gtcc.credit_available
        validated_data['previous_balance'] = credit_available
        validated_data['new_balance'] = credit_available + amount
        if amount > 100000:
            validated_data['status'] = 'Pending Approval'
        payment_detail = PaymentDetail.objects.create(**validated_data)
        if amount <= 100000:
            gtcc.credit_available = credit_available + amount
            gtcc.save()
        return payment_detail

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        if status not in ['Approved', 'Canceled']:
            raise serializers.ValidationError("Invalid status")
        if instance.status != 'Pending Approval':
            raise serializers.ValidationError("This details already approved/canceled")
        gtcc   = instance.gtcc
        amount = instance.amount
        instance.status = status
        instance.save()
        if status == 'Approved':
            gtcc.credit_available += amount
            gtcc.save()
        return instance
        
class PaymentListSerializer(serializers.ModelSerializer):
    mode_of_payment = ModeOfPaymentListSerializer()
    created_by = UserLimitedDetailSerializer()
    class Meta:
        model = PaymentDetail
        exclude = ['created_date', 'modified_by', 'modified_date']

class VehiclePostSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
      rfid_card = validated_data.pop("rfid_card", None)
      rfid_card_flag = 0
      if rfid_card is not None:
        try:
            rfid_card_obj = RFIDCard.objects.get(id=rfid_card)
        except RFIDCard.DoesNotExist:
            raise serializers.ValidationError("RFID not found")
        if rfid_card_obj.status != 'Active':
            raise serializers.ValidationError("RFID is not active")
        if rfid_card_obj.vehicle is not None:
            raise serializers.ValidationError("RFID is already assigned with a vehicle")
        rfid_card_flag = 1
      vehicle = VehicleDetail.objects.create(**validated_data, random_key = get_random_string(64).lower())
      if rfid_card_flag:
        rfid_card_obj.vehicle = vehicle
        rfid_card_obj.save()
      return vehicle

    rfid_card = serializers.IntegerField(required=False)
    class Meta:
        model = VehicleDetail
        exclude = ['random_key', 'created_by']

class VehicleListSerializer(serializers.ModelSerializer):
    driver = UserLimitedDetailSerializer()
    gtcc = GTCCLimitedDetailsListSerializer()
    rfid_vehicle = RFIDCardLimitedListSerializer()
    class Meta:
        model = VehicleDetail
        exclude = common_exclude_list

class VehicleLimitedListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDetail
        fields = ('id', 'vehicle_no', 'status')

class GTCCAndDriversListSerializer(serializers.ModelSerializer):
    vehicle_detail_gtcc = VehicleLimitedListSerializer(many=True)
    class Meta:
        model = GTCC
        fields = ['id', 'establishment_name', 'status','vehicle_detail_gtcc']

class GTCCDetailSerializer(serializers.ModelSerializer):
    active_contact_person = UserLimitedDetailSerializer()
    payment_detail_gtcc = PaymentListSerializer(many=True)
    vehicle_detail_gtcc = VehicleListSerializer(many=True)
    class Meta:
        model = GTCC
        exclude = common_exclude_list

class DriverPostSerializer(serializers.Serializer):
    gtcc = serializers.IntegerField()
    name = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=20, min_length=8, required=False)
    contact_number = serializers.CharField(max_length=50)
    license_no = serializers.CharField(max_length=50)
    emirate = serializers.CharField(max_length=50)

    def create(self, validated_data):
        gtcc    = validated_data.get('gtcc')
        try:
            gtcc_obj = GTCC.objects.get(pk=gtcc)
        except GTCC.DoesNotExist:
            raise serializers.ValidationError("GTCC not found")
        try:
            max_id = Account.objects.filter(user_class='GTCC', user_type='Driver').latest('id').id + 1001
        except Account.DoesNotExist:
            max_id = 1001
        username = "D" + str(max_id)
        first_name, last_name = name_maker(validated_data.get('name'))
        driver = Account.objects.create(
                    inviter             =   validated_data.get('created_by'),
                    email               =   username+"@email.com",
                    username            =   username,
                    first_name          =   first_name,
                    last_name           =   last_name,
                    password            =   make_password(validated_data.get('password')),
                    emirate             =   validated_data.get('emirate'),
                    license_no          =   validated_data.get('license_no'),
                    contact_number      =   validated_data.get('contact_number'),
                    link_id             =   gtcc,
                    link_class          =   'GTCC',
                    user_class          =   'GTCC',
                    user_type           =   'Driver',
                    user_status         =   'Activated')
        return driver

    def update(self, instance, validated_data):
        gtcc = validated_data.get('gtcc')
        try:
            gtcc_obj = GTCC.objects.get(pk=gtcc)
        except GTCC.DoesNotExist:
            raise serializers.ValidationError("GTCC not found")
        first_name, last_name = name_maker(validated_data.get('name'))
        instance.first_name = first_name
        instance.last_name = last_name
        instance.emirate = validated_data.get('emirate')
        instance.license_no = validated_data.get('license_no')
        instance.contact_number = validated_data.get('contact_number')
        instance.modified_by = validated_data.get('modified_by')
        instance.save()
        return instance

class DriverListSerializer(serializers.ModelSerializer):
    assigned_vehicle = VehicleListSerializer()
    name = serializers.CharField(source="full_name")
    class Meta:
        model = Account
        fields = ['id','username','name','contact_number','assigned_vehicle','license_no','emirate','user_status']

class VehicleQRCodeScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDetail
        fields = ['random_key']

    def create(self, validated_data):
        random_key = validated_data.get('random_key')
        driver = validated_data.get('driver')
        vehicle = VehicleDetail.objects.filter(random_key=random_key, status='Active').first()
        if not vehicle:
            raise serializers.ValidationError("Invalid QR Code !")
        # breakpoint()
        if(driver.link_id != vehicle.gtcc.id):
            raise serializers.ValidationError("Unauthorized !")
        driver.assigned_vehicle = vehicle
        driver.save()
        vehicle.driver = driver
        vehicle.save()
        service_requests = ServiceRequest.objects.filter(vehicle=vehicle, status='Assigned')
        if len(service_requests) != 0:
            for service_request in service_requests:
                service_request_driver = service_request.driver
                if service_request_driver != None:
                    ServiceRequestLog.objects.create(
                        service_request = service_request,
                        vehicle = vehicle,
                        driver = service_request_driver,
                        type = "Driver Unassigned",
                        log = f"Driver Mr.({service_request_driver.full_name}) is unassigned",
                        created_by = driver
                    )
                service_request.driver = driver
                service_request.save()
                ServiceRequestLog.objects.create(
                    service_request = service_request,
                    vehicle = vehicle,
                    driver = driver,
                    type = "Driver Assigned",
                    log = f"Driver Mr.({driver.full_name}) is assigned by scanning the QR code",
                    created_by = driver
                )
        return vehicle

class AssignVehicleForServiceRequestSerializer(serializers.Serializer):
    service_request = serializers.IntegerField()
    vehicle = serializers.IntegerField()

    def create(self, validated_data):
        service_request = validated_data.get('service_request')
        vehicle = validated_data.get("vehicle")

        try:
            service_request_data = ServiceRequest.objects.get(pk=service_request)
        except ServiceRequest.DoesNotExist:
            raise serializers.ValidationError("Service request not found")

        vehicle_data = VehicleDetail.objects.filter(pk=vehicle, status = 'Active').first()
        if vehicle_data is None:
            raise serializers.ValidationError("Vehicle not found")
        gtcc                    = service_request_data.entity_gtcc.gtcc
        active_gtcc_detail      = service_request_data.entity.active_gtcc_detail
        if gtcc != vehicle_data.gtcc:
            raise serializers.ValidationError("This vehicle not exist in the current GTCC")

        if active_gtcc_detail == None:
            raise serializers.ValidationError("There is no active contract")

        if active_gtcc_detail.status != 'Active':
            raise serializers.ValidationError("There is no active contract")

        if active_gtcc_detail.gtcc != gtcc:
            raise serializers.ValidationError("There is no active contract")

        user_data = validated_data.get('modified_by')

        service_request_status = service_request_data.status

        if service_request_status == 'Initiated' or service_request_status == 'Assigned':
            if service_request_status == 'Initiated':
                request_type = 'Assigned'
            else:
                request_type = 'Re-assigned'
            service_request_data.vehicle        = vehicle_data
            service_request_data.modified_by    = user_data
            service_request_data.status         = 'Assigned'
            service_request_data.save()
            ServiceRequestLog.objects.create(
                service_request = service_request_data,
                vehicle = vehicle_data,
                type = request_type,
                log = f'{request_type} to vehicle ({vehicle_data.vehicle_no}) by {user_data.full_name}',
                created_by = user_data
            )
            return service_request_data
        else:
            raise serializers.ValidationError("Vehicle already assigned for this service request")

class BookletPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booklet
        exclude = ['created_by']

class BookletListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booklet
        exclude = common_exclude_list

class CouponBookletPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponBooklet
        exclude = ['coupon_end_no', 'total_coupons', 'created_by']

    def create(self, validated_data):
        booklet = validated_data.get("booklet")
        coupon_start_no = booklet.coupon_start_no
        total_coupons = 50
        coupon_end_no = coupon_start_no + (total_coupons - 1)
        coupons = list(range(coupon_start_no, coupon_end_no+1))
        check_coupon_exist = Coupon.objects.filter(coupon_no__in = coupons)
        if len(check_coupon_exist) != 0:
            raise serializers.ValidationError("Coupon already exist")
        validated_data['coupon_end_no'] = coupon_end_no
        validated_data['total_coupons'] = total_coupons
        coupon_booklet = CouponBooklet.objects.create(**validated_data)
        for coupon in coupons:
            Coupon.objects.create(booklet=coupon_booklet, coupon_no=coupon)
        booklet.status = 'Issued'
        booklet.save()
        return coupon_booklet

    def update(self, instance, validated_data):
        gtcc = validated_data.get('gtcc', instance.gtcc)
        vehicle = validated_data.get('vehicle', instance.vehicle)
        collected_by = validated_data.get('collected_by', instance.collected_by)
        collected_on = validated_data.get('collected_on', instance.collected_on)
        modified_by = validated_data.get('modified_by')
        status = validated_data.get('status')
        if instance.status != 'Issued' and status == 'Deleted':
            raise serializers.ValidationError("You cannot delete this booklet. Because this is already in use/used")
        if status == None:
            status = instance.status
        instance.gtcc = gtcc
        instance.vehicle = vehicle
        instance.collected_by = collected_by
        instance.collected_on = collected_on
        instance.modified_by = modified_by
        instance.status = status
        instance.save()
        return instance
        
class CouponBookletListSerializer(serializers.ModelSerializer):
    gtcc        = GTCCLimitedDetailsListSerializer()
    vehicle     = VehicleLimitedListSerializer()
    created_by  = UserLimitedDetailSerializer()
    booklet     = BookletListSerializer()
    
    class Meta:
        model = CouponBooklet
        exclude = ['created_date', 'modified_by', 'modified_date']

class CouponListSerializer(serializers.ModelSerializer):
    collected_by = UserLimitedDetailSerializer()
    converted_by = UserLimitedDetailSerializer()
    class Meta:
        model = Coupon
        exclude = ['booklet']

class VehicleEntryDetailsSerializer(serializers.ModelSerializer):
    vehicle = VehicleListSerializer()
    driver = UserLimitedDetailSerializer()
    gtcc = GTCCLimitedDetailsListSerializer()

    class Meta:
        model = VehicleEntryDetails
        fields = '__all__'

class VehicleEntryDetailsLimitedSerializer(serializers.ModelSerializer):

    class Meta:
        model = VehicleEntryDetails
        fields = '__all__'
        
class CouponListSerializerLimited(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        exclude = ['returned_on', 'returned_by', 'collected_by', 'collected_remark', 'collection_violation', 'vehicle', 'dumping_vehicledetails', 'status' ]

class CouponListDetailedSerializer(serializers.ModelSerializer):
    booklet = CouponBookletListSerializer()
    returned_by = UserLimitedDetailSerializer()
    collected_by = UserLimitedDetailSerializer()
    converted_by = UserLimitedDetailSerializer()
    dumping_vehicledetails = VehicleEntryDetailsLimitedSerializer()
    class Meta:
        model = Coupon
        fields = '__all__'

class EditCouponLogSerializer(serializers.ModelSerializer):
    coupon = CouponListSerializerLimited()
    edited_by = UserLimitedDetailSerializer()
    class Meta:
        model = EditCouponLog
        fields = '__all__'