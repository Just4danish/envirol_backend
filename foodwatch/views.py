from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework import status
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.http import Http404
from django.core.exceptions import ValidationError
from entity.models import Entity, EntityGTCC, EntityGreaseTrap, ServiceRequest, ServiceRequestDetail, ServiceRequestLog
from foodwatch.serializers import ServiceRequestPostSerializer, EntityListSerializer, EntityGreaseTrapListSerializer
from .models import FoodwatchEntity, APILog
from gtcc.models import GTCC
from users.models import Account
from masters.models import SubCategory, SubArea, Designation
from users.serializers import LoginSerializer
from .serializers import FoodwatchEntitySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from abacimodules.permissions import IsFoodwatchUser
from django.utils.crypto import get_random_string
from abacimodules.abacifunctions import name_maker
from django.db import transaction
import json
import requests
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
        
def get_foodwatch_token():
    url     = f"{settings.FOODWATCH_BASE_URL}/login/getToken"
    payload = f'Username={settings.FOODWATCH_USERNAME}&Password={settings.FOODWATCH_PASSWORD}&Apikey={settings.FOODWATCH_APIKEY}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response    = requests.request("POST", url, headers=headers, data=payload)
    json_object = json.loads(response.text)
    token       = json_object['Result']['token']
    return token

def get_foodwatch_enitity():
    url     = f"{settings.FOODWATCH_BASE_URL}/api/v1/entityInfo?LastSyncDateTime=1670869800&EntityClassId=0&PageIndex=1"

    payload = {}
    files   = {}
    token   = get_foodwatch_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers, data=payload, files=files)
    api_log  = APILog.objects.create(url = url)
    return {
        "data"      : response,
        "api_log"   : api_log
    }

def submit_service_request(entity_id, equipment_label, source = 'FGW'):
    url     = f"{settings.FOODWATCH_BASE_URL}/api/v1/greasetrap/submitServiceRequest?EntityId={entity_id}&EquipmentLabel={equipment_label}&Source={source}"

    payload = {}
    files   = {}
    token   = get_foodwatch_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    api_log  = APILog.objects.create(url = url)
    return {
        "data"      : response,
        "api_log"   : api_log
    }

def tag_equipment(entity_id, equipment_label):
    url     = f"{settings.FOODWATCH_BASE_URL}/api/v1/greasetrap/tagEquipment?EquipmentLabel={equipment_label}&EntityId={entity_id}"

    payload = {}
    files   = {}
    token   = get_foodwatch_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    api_log  = APILog.objects.create(url = url)
    return {
        "data"      : response,
        "api_log"   : api_log
    }

def save_api_log(api_response):
    response        = api_response['data']
    api_log         = api_response['api_log']
    if response.status_code == 200:
        json_object = json.loads(response.text)
        if json_object['ResultCode'] == 200:
            api_log.status = 'Success'
        else:
            api_log.status = 'Failed'
        api_log.response      = json_object
    else:
        api_log.response    = "Failed to connect"
        api_log.status      = 'Failed'
    api_log.response_time = timezone.now()
    api_log.save()

def sync_foodwatch_enitity(request):
    api_response    = get_foodwatch_enitity()
    save_api_log(api_response)
    response        = api_response['data']
    if response:
        if response.status_code == 200:
            json_object = json.loads(response.text)
            if json_object['ResultCode'] == 200:
                TotalCount  = json_object['Result']['TotalCount']
                pages       = int(TotalCount / 100) + (1 if TotalCount % 100 > 0 else 0)
                sync_count  = 0
                for PageIndex in range(pages):
                    result = json_object['Result']
                    if result is not None:
                        entity_list   = result['EntityList']
                        for entity in entity_list:
                            entity_class_id         = entity['EntityClassId']
                            sub_category_id         = entity['SubCategoryId']
                            uae_region_id           = entity['UAERegionId']
                            foodwatch_id            = entity['FoodwatchId']
                            name_of_establishment   = entity['NameOfEstablishment']
                            license_nr              = entity['LicenseNr']
                            business_id             = entity['BusinessId'] if entity['BusinessId'] else 0
                            address                 = entity['Address']
                            po_box                  = entity['POBox']
                            office_line             = entity['OfficeLine']
                            office_email            = entity['OfficeEmail']
                            makani_nr               = entity['MakaniNr'] if entity['MakaniNr'] else 0
                            gtcc_foodwatch_id       = entity['GTTCFoodwatchId'] if entity['GTTCFoodwatchId'] else 0
                            fogwatch_sub_category   = SubCategory.objects.filter(foodwatch_id=entity_class_id, foodwatch_sub_id=sub_category_id).first()
                            fogwatch_sub_area       = SubArea.objects.filter(foodwatch_id=uae_region_id).first()
                            entity                  = Entity.objects.filter(foodwatch_id=foodwatch_id).first()
                            if entity is not None:
                                active_gtcc_detail = None
                                if gtcc_foodwatch_id != 0:
                                    gtcc  = GTCC.objects.filter(foodwatch_id=gtcc_foodwatch_id).first()
                                    if gtcc is not None:
                                        active_gtcc_detail  = entity.active_gtcc_detail
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
                                status = 'Synced'
                                entity.trade_license_no     = license_nr
                                entity.trade_license_name   = name_of_establishment
                                entity.active_gtcc_detail   = active_gtcc_detail
                                entity.business_id          = business_id
                                entity.address              = address
                                entity.po_box               = po_box
                                entity.phone_no             = office_line
                                entity.office_email         = office_email
                                entity.save()
                            else:
                                status = 'Pending'
                            FoodwatchEntity.objects.create(
                                foodwatch_id            = foodwatch_id,
                                business_id             = business_id,
                                name_of_establishment   = name_of_establishment,
                                license_nr              = license_nr,
                                gtcc_foodwatch_id       = entity['GTTCFoodwatchId'] if entity['GTTCFoodwatchId'] else 0,
                                entity_class_id         = entity_class_id,
                                entity_class            = entity['EntityClass'],
                                fogwatch_category       = fogwatch_sub_category.main_category if fogwatch_sub_category else None,
                                fogwatch_sub_category   = fogwatch_sub_category,
                                address                 = address,
                                po_box                  = po_box,
                                office_line             = office_line,
                                office_email            = office_email,
                                makani_nr               = makani_nr,
                                latitue_longitude       = entity['LatitueLongitude'],
                                category_id             = entity['CategoryId'],
                                category                = entity['Category'],
                                sub_category_id         = sub_category_id,
                                sub_category            = entity['SubCategory'],
                                website_url             = entity['WebsiteUrl'],
                                office_mobile           = entity['OfficeMobile'],
                                qr_code                 = entity['QRCode'],
                                uae_region_id           = uae_region_id,
                                uae_region_name         = entity['UAERegionName'],
                                fogwatch_zone           = fogwatch_sub_area.zone if fogwatch_sub_area else None,
                                fogwatch_area           = fogwatch_sub_area.area if fogwatch_sub_area else None,
                                fogwatch_sub_area       = fogwatch_sub_area,
                                status                  = status,
                            )
                            sync_count += 1
                    if PageIndex + 2 > pages:
                        break
                    api_response    = get_foodwatch_enitity()
                    save_api_log(api_response)
                    response        = api_response['data']
                    if response:
                        if response.status_code == 200:
                            json_object = json.loads(response.text)
                            if json_object['ResultCode'] == 200:
                                continue
                            else:
                                return HttpResponse(json_object['ResultDesc'])
                        else:
                            return HttpResponse("Failed to connect")
                    else:
                        return HttpResponse("Failed to connect")
                return HttpResponse(f"Total synced entity : {sync_count}")
            else:
                return HttpResponse(json_object['ResultDesc'])
        else:
            return HttpResponse("Failed to connect")
    else:
        return HttpResponse("Failed to connect")

class EntityList(APIView):

    def get(self, request):
        data = FoodwatchEntity.objects.exclude(status="Deleted")
        serializer = FoodwatchEntitySerializer(data, many=True).data
        return Response(serializer)

class EntityDetails(APIView):
    
    def get_object(self, pk):
        try:
            return FoodwatchEntity.objects.exclude(status='Deleted').get(pk=pk)
        except FoodwatchEntity.DoesNotExist:
            raise Http404

    def put(self, request, pk):
        data = self.get_object(pk)
        serializer = FoodwatchEntitySerializer(data, data=request.data)
        if serializer.is_valid():
            data = serializer.save(modified_by = request.user, is_convertable=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteEntity(APIView):
    
    def get_object(self, pk):
        try:
            return FoodwatchEntity.objects.exclude(status='Deleted').get(pk=pk)
        except FoodwatchEntity.DoesNotExist:
            raise Http404

    def put(self, request, pk):
        data                = self.get_object(pk)
        data.status         = 'Deleted'
        data.modified_by    = request.user
        data.save()
        return Response("Deleted", status=status.HTTP_200_OK)

class ConvertEntity(APIView):
    
    def get_object(self, pk):
        try:
            return FoodwatchEntity.objects.exclude(status='Converted').exclude(status='Deleted').get(pk=pk, is_convertable = True)
        except FoodwatchEntity.DoesNotExist:
            raise Http404

    @transaction.atomic
    def put(self, request, pk):
        foodwatch_entity    = self.get_object(pk)
        contact_person      = request.data.get('contact_person',None)
        contact_number      = request.data.get('contact_number',None)
        email               = request.data.get('email',None)
        emirate             = request.data.get('emirate',None)
        designation         = request.data.get('designation',None)
        if contact_person == None:
            return Response({'error' : 'Contact person is required'}, status=status.HTTP_400_BAD_REQUEST)
        if email == None:
            return Response({'error' : 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        check_email = Account.objects.filter(email=email).first()
        if check_email:
            return Response({'error' : 'User with this email id already exist'}, status=status.HTTP_400_BAD_REQUEST)
        if designation is not None:
            designation = Designation.objects.get(pk=designation)
        gtcc_foodwatch_id = foodwatch_entity.gtcc_foodwatch_id
        entity = Entity.objects.create(
            establishment_name      = foodwatch_entity.name_of_establishment,
            trade_license_no        = foodwatch_entity.license_nr,
            trade_license_name      = foodwatch_entity.name_of_establishment,
            foodwatch_id            = foodwatch_entity.foodwatch_id,
            foodwatch_business_id   = foodwatch_entity.business_id,
            category                = foodwatch_entity.fogwatch_category,
            sub_category            = foodwatch_entity.fogwatch_sub_category,
            makhani_no              = foodwatch_entity.makani_nr,
            zone                    = foodwatch_entity.fogwatch_zone,
            area                    = foodwatch_entity.fogwatch_area,
            subarea                 = foodwatch_entity.fogwatch_sub_area,
            address                 = foodwatch_entity.address,
            phone_no                = foodwatch_entity.office_line,
            office_email            = foodwatch_entity.office_email,
            po_box                  = foodwatch_entity.po_box,
            gps_coordinates         = foodwatch_entity.latitue_longitude,
            random_key              = get_random_string(64).lower(),
            created_by              = request.user
        )
        active_gtcc_detail = None
        if gtcc_foodwatch_id != 0:
            gtcc = GTCC.objects.filter(foodwatch_id=gtcc_foodwatch_id).first()
            if gtcc is not None:
                active_gtcc_detail = create_entity_gtcc(entity, gtcc, request.user)
                
        first_name, last_name = name_maker(contact_person)
        active_contact_person = Account.objects.create(
                inviter             =   request.user,
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
        foodwatch_entity.active_contact_person  = active_contact_person
        foodwatch_entity.status                 = 'Converted'
        foodwatch_entity.save()
        entity.active_contact_person    = active_contact_person
        entity.active_gtcc_detail       = active_gtcc_detail
        entity.save()
        return Response(FoodwatchEntitySerializer(foodwatch_entity).data)