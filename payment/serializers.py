from rest_framework import serializers
from gtcc.models import CheckoutDetail
from gtcc.serializers import GTCCDropdownListSerializer
from users.serializers import UserSerializer

class CheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutDetail
        exclude = ['gtcc', 'payload', 'response', 'created_by']

class CheckoutListSerializer(serializers.ModelSerializer):
    gtcc = GTCCDropdownListSerializer()
    created_by = UserSerializer()
    class Meta:
        model = CheckoutDetail
        fields = '__all__'