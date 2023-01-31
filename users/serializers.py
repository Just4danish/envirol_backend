from rest_framework import serializers
from .models import Account, LoginDetail
from django.contrib.auth.models import User
from masters.serializers import DesignationListSerializer
from rest_framework.validators import UniqueValidator

class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=20, min_length=8, write_only=True)
    username = serializers.CharField(max_length=255, min_length=2)

    class Meta:
        model = User
        fields = ['email', 'password']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["last_login","email","username","first_name","last_name","avatar"]

class UserLimitedDetailSerializer(serializers.ModelSerializer):
    designation = DesignationListSerializer()
    class Meta:
        model = Account
        fields = ["id","full_name","email","contact_number", "designation","emirate","user_status","avatar"]

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"

class AccountEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[UniqueValidator(queryset=Account.objects.all())])
               
class AccountSerializer(serializers.ModelSerializer):
    designation = DesignationListSerializer()
    class Meta:
        model = Account
        extra_kwargs = {'password': {'write_only': True}}
        exclude = ('retrieve_password_otp', 'inviting_key', 'registration_key','invited_date', 'invite_expiry_date',)

class InvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    user_class = serializers.CharField()
    user_type = serializers.CharField()

class ActivateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=8,
        max_length=20,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )

class OTPValidateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

class ForgotPasswordSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    password = serializers.CharField(
        min_length=8,
        max_length=20,
        write_only=True,
        required=True,
        )

class OperatorPasswordSerializer(serializers.Serializer):
    operator_id = serializers.IntegerField(required=True)
    password = serializers.CharField(
        min_length=8,
        max_length=20,
        write_only=True,
        required=True,
        )

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        min_length=8,
        max_length=20,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )
    new_password = serializers.CharField(
        min_length=8,
        max_length=20,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )

class CreateOperatorSerializer(serializers.Serializer):
    pk = serializers.IntegerField(
        required=False,
    )
    mobile_number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(
        required=False,
    )
    password = serializers.CharField(
        min_length=8,
        max_length=20,
        write_only=True,
        required=True,
        help_text='Leave empty if no change needed',
        style={'input_type': 'password', 'placeholder': 'Password'}
    )

class LoginDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = LoginDetail
        fields = "__all__"

class InviteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        exclude =('username', 'password',)
