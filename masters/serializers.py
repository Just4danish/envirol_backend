from rest_framework import serializers
from .models import *
from gtcc.models import GTCC

common_exclude_list = ['created_by', 'created_date', 'modified_by', 'modified_date']

class MainCategoryPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainCategory
        exclude = ['created_by']

class MainCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainCategory
        exclude = common_exclude_list

class SubCategoryPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        exclude = ['created_by']

class SubCategoryListSerializer(serializers.ModelSerializer):
    main_category = MainCategoryListSerializer()
    class Meta:
        model = SubCategory
        exclude = common_exclude_list

class ModeOfPaymentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeOfPayment
        exclude = ['mop_id', 'created_by']

class ModeOfPaymentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeOfPayment
        exclude = common_exclude_list

class GreaseTrapPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = GreaseTrap
        exclude = ['grease_trap_id', 'created_by']

class GreaseTrapListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GreaseTrap
        exclude = common_exclude_list

class GreaseTrapLimitedDetailsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GreaseTrap
        fields = ['id','trap_label','status']

class FixturePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fixture
        exclude = ['fixture_id', 'created_by']

class FixtureListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fixture
        exclude = common_exclude_list

class ZonePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        exclude = ['created_by']

class ZoneListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        exclude = common_exclude_list

class AreaPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        exclude = ['created_by']

class AreaListSerializer(serializers.ModelSerializer):
    zone = ZoneListSerializer()
    class Meta:
        model = Area
        exclude = common_exclude_list

class SubAreaPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubArea
        exclude = ['created_by']

class SubAreaListSerializer(serializers.ModelSerializer):
    area = AreaListSerializer()
    class Meta:
        model = SubArea
        exclude = ['created_by', 'created_date', 'modified_by', 'modified_date', 'zone']

class DesignationPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        exclude = ['created_by']

class DesignationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        exclude = common_exclude_list

class GatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gate
        exclude = ['created_by']

class GateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gate
        exclude = common_exclude_list

class RFIDCardPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDCard
        exclude = ['created_by']

class GTCCListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GTCC
        fields = ['id', 'establishment_name']

class VehicleLimitedListSerializer(serializers.ModelSerializer):
    gtcc = GTCCListSerializer()
    class Meta:
        model = VehicleDetail
        fields = ('id', 'vehicle_no', 'status','gtcc')

class RFIDCardListSerializer(serializers.ModelSerializer):
    vehicle = VehicleLimitedListSerializer()
    class Meta:
        model = RFIDCard
        exclude = common_exclude_list

class RFIDCardLimitedListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDCard
        fields = ('id', 'tag_id', 'friendly_name')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_by']