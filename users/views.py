from django.core.files import File as Files
from django.http import Http404
import datetime
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status, permissions
from abacimodules.abacifunctions import get_client_ip
from rest_framework.decorators import APIView
from .serializers import *
from .models import *
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from PIL import Image
from io import BytesIO
import base64
from django.conf import settings
import jwt
from django.db.models import Q
from gtcc.models import VehicleDetail
from entity.models import ServiceRequest
from gtcc.serializers import VehicleListSerializer
from entity.serializers import ServiceRequestListSerializer
from gtcc.views import unlink_vehicle_from_driver, vehicle_list_for_operator, allJobs_list_for_driver
from gtcc.models import GTCC
from gtcc.serializers import GTCCModelSerializer


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny, )
    def post(self, request):
        data      = request.data
        username  = data.get('username', '').lower()
        password  = data.get('password', '')
        user = Account.objects.filter(username = username).first()
        if isinstance(user, type(None)):
            LoginDetail.objects.create(
                ip_address  =   get_client_ip(request),
                status      =   'Failed',
                reason      =   f'User Not Found &{username}',
            )
            content = {'error': 'User not found !!!'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)
        else:
            if user.user_class == 'Foodwatch':
                LoginDetail.objects.create(
                    user        =   user,
                    ip_address  =   get_client_ip(request),
                    status      =   'Failed',
                    reason      =   'Foodwatch User',
                )
                content = {'error': 'User not found !!!'}
                return Response(content, status=status.HTTP_403_FORBIDDEN)
            if user.user_status == 'Deleted':
                LoginDetail.objects.create(
                    user        =   user,
                    ip_address  =   get_client_ip(request),
                    status      =   'Failed',
                    reason      =   'Deleted User',
                )
                content = {'error': 'User not found !!!'}
                return Response(content, status=status.HTTP_403_FORBIDDEN)
            password_validity = user.check_password(password)
            if (password_validity):
                if user.user_status == 'Deactivated':
                    LoginDetail.objects.create(
                        user        =   user,
                        ip_address  =   get_client_ip(request),
                        status      =   'Failed',
                        reason      =   'Deactivated User',
                    )
                    content = {'error': 'This account is deactivated. Please contact your administrator !!!'}
                    return Response(content, status=status.HTTP_403_FORBIDDEN)
                message = {
                            'username': user.username, 
                            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=settings.EXPIRY_IN_MINUTES)
                            }
                auth_token = jwt.encode(message, settings.JWT_SECRET_KEY, algorithm="HS256")
                serialized_data = AccountSerializer(user).data
                if (user.user_type == 'Driver'):
                    vehicle = VehicleDetail.objects.filter(driver=user, status = 'Active').first()
                    gtcc = GTCC.objects.get(id = user.link_id)
                    serialized_data['gtcc'] = GTCCModelSerializer(gtcc).data
                    if not vehicle:
                        serialized_data['vehicle_details'] = 'vehicle_inactive'
                    else:
                        serialized_data['vehicle_details'] = VehicleListSerializer(vehicle).data
                data = {'user': serialized_data, 'token': auth_token}
                response = Response()
                response.set_cookie(key='token', value=auth_token, httponly=False)
                response.data = data
                LoginDetail.objects.create(
                    user        =   user,
                    ip_address  =   get_client_ip(request),
                    status      =   'Success',
                    reason      =   'Active User',
                )
                user.last_login = timezone.now()
                user.save()
                return response
            else:
                LoginDetail.objects.create(
                    user        =   user,
                    ip_address  =   get_client_ip(request),
                    status      =   'Failed',
                    reason      =   'Invalid Password',
                )
                content = {'error': 'Invalid credentials !!!'}
                return Response(content, status=status.HTTP_403_FORBIDDEN)

class LogoutView(APIView):
    def post(self, request):
        user    = request.user
        unlink  = unlink_vehicle_from_driver(user)
        LoginDetail.objects.create(
                user        =   user,
                ip_address  =   "Not Available",
                log_type    =   'Logout',
                status      =   'Success',
        )
        return Response("User logged out successfully", status=status.HTTP_200_OK)

class InviteUserView(APIView):
    # permission_classes = [permissions.IsAdminUser]
    def post(self, request):
        serializer = InviteUserSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        temp_model = Account.objects.create(
                inviter             =   request.user,
                email               =   serializer.validated_data.get('email'),
                username            =   serializer.validated_data.get('email'),
                emp_id              =   serializer.validated_data.get('emp_id'),
                designation         =   serializer.validated_data.get('designation'),
                first_name          =   serializer.validated_data.get('first_name'),
                last_name           =   serializer.validated_data.get('last_name'),
                address             =   serializer.validated_data.get('address'),
                extension_number    =   serializer.validated_data.get('extension_number'),
                contact_number      =   serializer.validated_data.get('contact_number'),
                user_class          =   serializer.validated_data.get('user_class'),
                user_type           =   serializer.validated_data.get('user_type'),
                inviting_key        =   get_random_string(64).lower(),
                invited_date        =   timezone.now(),
                invite_expiry_date  =   (timezone.now() + datetime.timedelta(3)),)
        temp_model.send_invitation()
        content = {
            'message': 'User Invited Successfully !!!',
            'users': AccountSerializer(temp_model).data
            }
        return Response(content, status=status.HTTP_200_OK)

class ActivateInvitationView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, key, format=None):
        try:
            record = Account.objects.filter(inviting_key=key)
            if(len(record) == 0):
                content = {'error': 'Invitation not found !!!'}
                return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            else:
                user = record[0]
                if user.user_status != 'Invited':
                    content = {'error': 'Invited User is already Active !!!'}
                    return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
                else:
                    if (user.invite_expiry_date >= timezone.now()):
                        registration_key        = get_random_string(64).lower()
                        user.registration_key   = registration_key
                        user.save()
                        content = {
                            "registration_key": registration_key,
                            "email": user.email
                        }
                        return Response(content, status=status.HTTP_200_OK)
                    else:
                        content = {'error': 'The link is expired !!!'}
                        return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        except:
            content = {'error': 'Invitation not found !!!'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, key):
        serializer = ActivateUserSerializer(data=request.data)
        if serializer.is_valid():
            invitee_email = serializer.validated_data.get('email')
            qs = Account.objects.filter(email=invitee_email)
            if len(qs) == 0:
                content = {'error': 'Invitation not found !!!'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            elif qs[0].registration_key != key:
                content = {'error': 'Invalid registration key !!!'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            elif qs[0].user_status != 'Invited':
                content = {'error': 'User already activated !!!'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            else:
                record = qs[0]

                record.user_status          = "Activated"
                record.password             = make_password(serializer.validated_data.get('password'))
                record.save()
                content = {'Success': 'User Activated Successfully !!!'}
                if record.user_class == 'Foodwatch':
                    record.send_api_key()
                return Response(content, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            password  =  make_password(serializer.validated_data.get('password'))
            data = serializer.save(inviter = request.user, password = password, user_status = "Activated")
            return Response(AccountSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetails(APIView):

    def get_object(self, pk):
        try:
            return Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = AccountSerializer(data)
        return Response(serializer.data)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = CreateUserSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            password = request.data.get('password', None)
            if password is not None:
                password  =  make_password(password)
                serializer.save(modified_by = request.user, password=password)
            else:
                serializer.save(modified_by = request.user)
            return Response(AccountSerializer(data).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EnvirolUserView(APIView):
    def get(self, request):
        users = Account.objects.filter(user_class = 'Envirol').filter(Q(user_type = 'Admin') | Q(user_type = 'User')).exclude(user_status="Deleted").exclude(id=request.user.id)
        return Response(AccountSerializer(users, many=True).data, status=status.HTTP_200_OK)

class FoodwatchUserView(APIView):
    def get(self, request):
        users = Account.objects.filter(user_class = 'Foodwatch').filter(Q(user_type = 'Admin') | Q(user_type = 'User')).exclude(user_status="Deleted")
        return Response(AccountSerializer(users, many=True).data, status=status.HTTP_200_OK)

class GateOperatorView(APIView):
    def get(self, request):
        users = Account.objects.filter(user_class = 'Envirol', user_type = 'Operator').exclude(user_status="Deleted").exclude(id=request.user.id)
        return Response(AccountSerializer(users, many=True).data, status=status.HTTP_200_OK)

class InspectorView(APIView):
    def get(self, request):
        users = Account.objects.filter(user_class = 'Envirol', user_type = 'Inspector').exclude(user_status="Deleted").exclude(id=request.user.id)
        return Response(AccountSerializer(users, many=True).data, status=status.HTTP_200_OK)

class SendForgotPasswordOTP(APIView):
    permission_classes = (permissions.AllowAny, )
    
    def post(self, request):
        data = request.data
        email    = data.get('email', '')
        user = Account.objects.filter(email = email).first()
        if isinstance(user, type(None)):
            content = {'error': 'User not found !!!'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)
        else:
            if user.user_status != "Activated":
                content = {'error': 'This is not an active user !!!'}
                return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            user.forgot_password()
            content = {'message': 'OTP sent successfully !!!'}
            return Response(content, status=status.HTTP_200_OK)

class ValidateForgotPasswordOTP(APIView):
    permission_classes = (permissions.AllowAny, )
    
    def post(self, request):
        data = request.data
        serializer = OTPValidateSerializer(data=data)
        if serializer.is_valid():
            email           = serializer.validated_data.get('email')
            entered_otp     = serializer.validated_data.get('otp')
            user = Account.objects.filter(email = email).first()
            if isinstance(user, type(None)):
                content = {'error': 'User not found !!!'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            else:
                if user.user_status != "Activated":
                    content = {'error': 'This is not an active user !!!'}
                    return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
                if(user.retrieve_password_otp != ""):
                    if (user.retrieve_password_otp_expired):
                        content = {'error': "OTP has been expired or incorrect"}
                        return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
                    if(user.retrieve_password_otp != int(entered_otp)):
                        user.retrieve_password_otp_expired = True
                        user.save()
                        content = {'error': "Invalid OTP"}
                        return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
                    else:
                        user.retrieve_password_otp_expired = True
                        user.save()
                        content = {
                                    'message': 'OTP validate successfully !!!',
                                    'registration_key': user.registration_key
                                    }
                        return Response(content, status=status.HTTP_200_OK)
                else:
                    content = {'error': 'OTP validation failed !!!'}
                    return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data.get('old_password')
            new_password = serializer.validated_data.get('new_password')
            if(request.user.check_password(old_password)):
                request.user.password = make_password(new_password)
                request.user.save()
                content = {'Success': 'Password Updated Successfully !'}
                return Response(content, status=status.HTTP_200_OK)
            else:
                content = {
                    'error': 'Old password provided is not matching !'}
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)
        else:
            content = {'error': serializer.errors}
            return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)

class ResendInvitationView(APIView):

    def get_object(self, pk):
        try:
            return Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            raise Http404

    def put(self, request, pk):
        record = self.get_object(pk)
        if record.user_status == 'Invited':
            record.inviting_key        =   get_random_string(64).lower()
            record.invite_expiry_date  =   (timezone.now() + datetime.timedelta(3))
            record.modified_by         =   request.user
            record.save()
            record.send_invitation()
            content = {'Success': 'Invitation Resend Successfully !!!'}
            return Response(content, status=status.HTTP_202_ACCEPTED)
        else:
            content = {'error': 'User already activated !!!'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

class ProfileView(APIView):
    def get(self, request):
        userobject = request.user
        serialized_data = AccountSerializer(userobject).data
        if (userobject.user_type == 'Driver'):
            vehicle = VehicleDetail.objects.filter(driver=userobject, status = 'Active').first()
            gtcc = GTCC.objects.get(id = userobject.link_id)
            serialized_data['gtcc'] = GTCCModelSerializer(gtcc).data
            if not vehicle:
                serialized_data['vehicle_details'] = 'vehicle_inactive'
            else:
                serialized_data['vehicle_details'] = VehicleListSerializer(vehicle).data
        return Response(serialized_data, status=status.HTTP_200_OK)


    def post(self, request):
        userobject = request.user
        if 'avatar' in request.data and request.data['avatar'] != "":
            avatar_data = request.data['avatar'].split(',')[1]
            avatar = Image.open(BytesIO(base64.b64decode(avatar_data)))
            if avatar.width > 200:
                avatar = avatar.resize((200, 200))
            avatar = avatar.convert('RGB')
            blob = BytesIO()
            avatar.save(blob, 'JPEG')
            avatar = Files(blob)
            userobject.avatar.save('name.jpg', avatar)
        
        if 'first_name' in request.data and request.data['first_name'] != "":
            first_name = request.data['first_name']
        else:
            first_name = userobject.first_name
        if 'last_name' in request.data and request.data['last_name'] != "":
            last_name = request.data['last_name']
        else:
            last_name = userobject.last_name
            
        userobject.first_name = first_name
        userobject.last_name = last_name
        userobject.modified_by = request.user
        userobject.save()
        
        content = AccountSerializer(userobject).data
        return Response(content, status=status.HTTP_202_ACCEPTED)
