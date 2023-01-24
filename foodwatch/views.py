from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from entity.models import Entity, EntityGTCC, EntityGreaseTrap, ServiceRequest, ServiceRequestDetail, ServiceRequestLog
from foodwatch.serializers import ServiceRequestPostSerializer, EntityListSerializer, EntityGreaseTrapListSerializer
from gtcc.models import GTCC
from users.models import Account
from users.serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from abacimodules.permissions import IsFoodwatchUser
from django.db import transaction
import datetime
import jwt

class GetToken(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        data      = request.data
        username  = data.get('username', '').lower()
        password  = data.get('password', '')
        api_key  = data.get('api_key', '')
        user = Account.objects.filter(username = username, user_class = 'Foodwatch').first()
        if isinstance(user, type(None)):
            content = {'error': 'User not found !!!'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)
        else:
            if user.user_status == 'Deleted':
                content = {'error': 'User not found !!!'}
                return Response(content, status=status.HTTP_403_FORBIDDEN)
            password_validity = user.check_password(password)
            if (password_validity):
                if user.api_key != api_key:
                    content = {'error': 'Invalid API Key !!!'}
                    return Response(content, status=status.HTTP_403_FORBIDDEN)
                if user.user_status == 'Deactivated':
                    content = {'error': 'This account is deactivated. Please contact your administrator !!!'}
                    return Response(content, status=status.HTTP_403_FORBIDDEN)
                message = {
                            'username': user.username, 
                            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=settings.EXPIRY_IN_MINUTES)
                            }
                auth_token = jwt.encode(message, settings.JWT_SECRET_KEY, algorithm="HS256")
                data = {
                    "ResultCode":200,
                    "ResultDesc":"Success",
                    "Result":{
                        "token" : auth_token
                    }
                }
                response = Response()
                response.data = data
                user.last_login = timezone.now()
                user.save()
                return response
            else:
                content = {'error': 'Invalid credentials !!!'}
                return Response(content, status=status.HTTP_403_FORBIDDEN)

def get_entity_from_foodwatch_id(foodwatch_id):
    entity = Entity.objects.filter(foodwatch_id=foodwatch_id).first()
    if isinstance(entity, type(None)):
        raise ValidationError("Entity not found")
    else:
        if entity.status == 'Active':
            return entity
        else:
            raise ValidationError("Entity not found")

def get_gtcc_from_foodwatch_id(foodwatch_id):
    gtcc = GTCC.objects.filter(foodwatch_id=foodwatch_id).first()
    if isinstance(gtcc, type(None)):
        raise ValidationError("GTCC not found")
    else:
        if gtcc.status == 'Active':
            return gtcc
        else:
            raise ValidationError("GTCC not found")

def create_entity_gtcc(entity, gtcc, user):
    active_gtcc_detail = EntityGTCC.objects.create(
                    entity = entity,
                    gtcc = gtcc,
                    created_by = user
                )
    entity.active_gtcc_detail = active_gtcc_detail
    entity.modified_by = user
    entity.save()
    return active_gtcc_detail

class EntityGreaseTrapList(APIView):
    permission_classes = [IsAuthenticated,IsFoodwatchUser]
    def post(self, request):
        data      = request.data
        entity_foodwatch_id  = data.get('entity_foodwatch_id', None)
        if entity_foodwatch_id is None:
            content = {'error': 'Foodwatch ID is required'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)
        entity = get_entity_from_foodwatch_id(entity_foodwatch_id)
        entity_grease_traps = EntityGreaseTrap.objects.filter(entity=entity, status='Active')
        result = EntityListSerializer(entity).data
        result['grease_trap_list'] = EntityGreaseTrapListSerializer(entity_grease_traps, many=True).data
        content = {
            "ResultCode":200,
            "ResultDesc":"Success",
            "Result":result
        }
        return Response(content, status=status.HTTP_200_OK)

class CreateServiceRequest(APIView):
    permission_classes = [IsAuthenticated, IsFoodwatchUser]

    @transaction.atomic
    def post(self, request):
        serializer =  ServiceRequestPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        entity_foodwatch_id = serializer.validated_data.get('entity_foodwatch_id')
        gtcc_foodwatch_id   = serializer.validated_data.get('gtcc_foodwatch_id')
        grease_traps        = serializer.validated_data.get('grease_traps')
        initiator           = serializer.validated_data.get('initiator')
        grease_traps_count  = len(grease_traps)
        if grease_traps_count == 0:
            content = {'error': 'Grease traps count should not be zero'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)
        if initiator not in ['FDW', 'IOT']:
            content = {'error': 'Invalid initiator'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)
        entity = get_entity_from_foodwatch_id(entity_foodwatch_id)
        gtcc = get_gtcc_from_foodwatch_id(gtcc_foodwatch_id)
        non_exist_count  = 0
        non_exist_list   = []
        grease_trap_list = []
        for grease_trap in grease_traps:
            try:
                grease_trap_data = EntityGreaseTrap.objects.get(grease_trap_label=grease_trap)
                grease_trap_list.append(grease_trap_data)
            except EntityGreaseTrap.DoesNotExist:
                non_exist_count += 1
                non_exist_list.append(grease_trap)
        if non_exist_count != 0:
            content = {'error': f'Grease trap(s) not found ({non_exist_list})'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)
        active_gtcc_detail = entity.active_gtcc_detail
        if active_gtcc_detail == None:
            active_gtcc_detail = create_entity_gtcc(entity, gtcc, request.user)
        else:
            if active_gtcc_detail.gtcc == gtcc:
                if active_gtcc_detail.status == 'Expired':
                    active_gtcc_detail = create_entity_gtcc(entity, gtcc, request.user)
            else:
                check_active_gtcc = EntityGTCC.objects.filter(entity=entity, status='Active').first()
                if check_active_gtcc:
                    check_active_gtcc.status = 'Expired'
                    check_active_gtcc.contract_end = datetime.date.today()
                    check_active_gtcc.save()
                active_gtcc_detail = create_entity_gtcc(entity, gtcc, request.user)
        service_request = ServiceRequest.objects.create(
            entity = entity, 
            entity_gtcc = active_gtcc_detail, 
            grease_trap_count = len(grease_traps),
            created_by = request.user
        )
        for grease_trap in grease_trap_list:
            ServiceRequestDetail.objects.create(
                service_request = service_request,
                grease_trap = grease_trap_data
            )
        ServiceRequestLog.objects.create(
            service_request = service_request,
            type = "Initiated",
            log = "Job initiated from "+entity.establishment_name,
            created_by = request.user
        )
        content = {
            "ResultCode":200,
            "ResultDesc":"Success",
            "Result":{
                "SRID" : service_request.id
            }
        }
        return Response(content, status=status.HTTP_200_OK)
