from rest_framework import serializers
from entity.models import Entity, EntityGreaseTrap
from masters.models import GreaseTrap
from .models import FoodwatchEntity
from masters.serializers import SubAreaListSerializer, SubCategoryListSerializer

class ServiceRequestPostSerializer(serializers.Serializer):
    entity_foodwatch_id = serializers.IntegerField()
    gtcc_foodwatch_id = serializers.IntegerField()
    grease_traps =  serializers.ListField()
    initiator = serializers.CharField()

class EntityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['establishment_name']

class GreaseTrapListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GreaseTrap
        fields = ['description', 'capacity', 'width', 'length', 'height', 'height_to_outlet_pipe']

class EntityGreaseTrapListSerializer(serializers.ModelSerializer):
    grease_trap = GreaseTrapListSerializer()
    class Meta:
        model = EntityGreaseTrap
        fields = ['capacity', 'grease_trap_label', 'grease_trap']

class FoodwatchEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodwatchEntity
        fields = '__all__'
        read_only_fields = ('foodwatch_id',)
