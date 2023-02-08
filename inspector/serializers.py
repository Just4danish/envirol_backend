from rest_framework import serializers
from masters.models import Zone, Area, SubArea
from entity.models import Entity

class ZoneListSerializer(serializers.ModelSerializer):
    area_count = serializers.SerializerMethodField()
    sub_area_count = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()
    class Meta:
        model = Zone
        fields = ['id','zone_no','zone_name','area_count','sub_area_count', 'entity']

    def get_area_count(self, obj):
        return obj.area_zone.filter(status='Active').count()

    def get_sub_area_count(self, obj):
        return obj.sub_area_zone.filter(status='Active').count()

    def get_entity(self, obj):
        entities = obj.entity_zone.filter(status='Active')
        return {
            "total_count" : entities.count(),
            "cleaned_count" : entities.filter(cleaning_status='Cleaned').count(),
            "due_count" : entities.filter(status='Due').count(),
            "overdue_count" : entities.filter(status='Overdue').count(),
        }

class AreaListSerializer(serializers.ModelSerializer):
    sub_area_count = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()
    class Meta:
        model = Area
        fields = ['id','area_code','area','sub_area_count', 'entity']

    def get_sub_area_count(self, obj):
        return obj.sub_area_area.filter(status='Active').count()

    def get_entity(self, obj):
        entities = obj.entity_area.filter(status='Active')
        return {
            "total_count" : entities.count(),
            "cleaned_count" : entities.filter(cleaning_status='Cleaned').count(),
            "due_count" : entities.filter(status='Due').count(),
            "overdue_count" : entities.filter(status='Overdue').count(),
        }

class SubAreaListSerializerInspector(serializers.ModelSerializer):
    entity = serializers.SerializerMethodField()
    class Meta:
        model = SubArea
        fields = ['id','sub_area','entity']

    def get_entity(self, obj):
        entities = obj.entity_subarea.filter(status='Active')
        return {
            "total_count" : entities.count(),
            "cleaned_count" : entities.filter(cleaning_status='Cleaned').count(),
            "due_count" : entities.filter(status='Due').count(),
            "overdue_count" : entities.filter(status='Overdue').count(),
        }

class EntityListSerializerInspector(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['id', 'establishment_name', 'trade_license_no', 'makhani_no', 'cleaning_status', 'inspection_status']