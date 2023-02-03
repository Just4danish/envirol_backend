from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status, generics, filters
from entity.models import ServiceRequestDetail, ServiceRequestDetailImage, EntityGTCC
from entity.serializers import ServiceRequestListSerializer, ServiceRequestDetailListSerializer, EntitySerializer, ServiceRequestSerializer, GTCCContractListSerializer
from masters.models import Unitprice
from .serializers import *
from django.http import Http404,HttpResponse
from django.db import transaction
from users.serializers import UserLimitedDetailSerializer, AccountEmailSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from abacimodules.permissions import IsDriver, IsOperator, IsGTCCUser
import decimal
import json
import pytz
from django.db import connection
import pandas as pd
from django.db.models import Sum, Count
from abacimodules.base import is_int
from django.db.models import Q

class GTCCList(generics.ListCreateAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields =     [
                        'establishment_name', 
                        'trade_license_no',
                        'env_sap_id',
                        'location',
                        'active_contact_person__full_name',
                        'office_email',
                        'status',
                        ]

    def get_queryset(self):
        records = GTCC.objects.exclude(status="Deleted")
        return records

    def get_df(self):
        self.pagination_class = None
        records = self.filter_queryset(self.get_queryset())
        users = Account.objects.all()
        df_records = pd.DataFrame.from_records(records.values_list( 
                                                                    'id',
                                                                    'trade_license_no', 
                                                                    'establishment_name',
                                                                    'env_sap_id', 
                                                                    'location', 
                                                                    'active_contact_person_id', 
                                                                    'status', 
                                                                   ))
        columns_records  = ['GTCC ID',
                    'License No', 
                    'GTCC Name',
                    'Business ID', 
                    'Location', 
                    'active_contact_person_id', 
                    'Status',]
        df_records.set_axis(columns_records, axis=1, inplace=True)
        df_users = pd.DataFrame.from_records(users.filter(user_class='GTCC').values_list('id','full_name', 'contact_number', 'email'))
        columns_users  = ['id',
                    'Contact Person', 
                    'Contact No',
                    'Email ID', ]
        df_users.set_axis(columns_users, axis=1, inplace=True)
        df = df_records.merge(df_users, how='inner', left_on='active_contact_person_id', right_on='id')
        df.drop(['active_contact_person_id','id'], inplace=True, axis=1)
        df.loc[:, ['GTCC ID',
                    'License No', 
                    'GTCC Name',
                    'Business ID', 
                    'Location', 
                    'Contact Person', 
                    'Email ID', 
                    'Contact No',
                    'Status',]]
        return df

    def get_serializer_class(self):
        limited = self.request.data.get('limited', False)
        if limited:
            return GTCCLimitedDetailsListSerializer
        else:
            return GTCCListSerializer
            
    def get(self, request):
        pdf_download = request.GET.get('pdf_download')
        csv_download = request.GET.get('csv_download')
        if (csv_download != None):
            df = self.get_df()
            df.set_index('GTCC ID', inplace=True)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=file.csv'
            df.to_csv(path_or_buf=response)
            return response
        elif (pdf_download != None):
            df = self.get_df()
            header = {
                'GTCC ID'	    :	'GTCC ID',
                'License No' 	:	'License No', 
                'GTCC Name'	    :	'GTCC Name',
                'Business ID' 	:	'Business ID', 
                'Location' 	    :	'Location', 
                'Contact Person':   'Contact Person', 
                'Email ID' 	    :	'Email ID', 
                'Contact No'	:	'Contact No',
                'Status'	    :	'Status'
            }
            data = {
                "header" : header,
                "body" : df.to_dict(orient='records'),
            }
            return Response(data, status=status.HTTP_200_OK)
        return super(GTCCList, self).get(request)

    @transaction.atomic
    def post(self, request):
        serializer = GTCCPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(GTCCListSerializer(data).data, status=status.HTTP_200_OK)

class GTCCDetails(APIView):
    def get_object(self, pk):
        try:
            return GTCC.objects.get(pk=pk)
        except GTCC.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = GTCCDetailSerializer(data).data
        drivers = Account.objects.filter(link_id=pk, link_class='GTCC', user_class='GTCC', user_type='Driver').exclude(user_status='DT')
        serializer['drivers'] = DriverListSerializer(drivers, many=True).data
        dumping_details = ServiceRequest.objects.filter(entity_gtcc__gtcc=data, status='Discharged')
        serializer['dumping_details'] = ServiceRequestListSerializer(dumping_details, many=True).data
        return Response(serializer)

    @transaction.atomic
    def put(self, request, pk):
        data = self.get_object(pk)
        serializer = GTCCPostSerializer(data, data=request.data)
        if serializer.is_valid():
            data = serializer.save(modified_by = request.user)
            return Response(GTCCListSerializer(data).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExcelOrCSVUploadView(APIView):
    def post(self, request):
        imported_file = request.data.get('imported_file', None)
        if imported_file is not None:
            df = pd.io.excel.read_excel(imported_file)
            received_fields = df.columns
            content = {
                "received_flelds" : received_fields,
                "received_file"   : json.loads(df.to_json(orient='records'))
            }
            return Response(content, status=status.HTTP_200_OK)
        else:
            return Response("File is required", status=status.HTTP_200_OK)

class ValidateImportGTCC(APIView):
    def post(self, request):
        datas           = request.data
        response_data   = []
        exist_count     = 0
        try:
            for data in datas:
                invitee_email                       = data['Contact Person Email Id']
                designation                         = data['Designation']
                establishment_name                  = data['Establishment Name']
                foodwatch_business_id               = data['FoodWatch Business Id'],
                foodwatch_id                        = data['FoodWatch Id'],
                trade_license_no                    = data['Trade License No']
                emirate_id                          = data['Emirate Id']
                data['establishment_name_status']   = ""
                data['trade_license_no_status']     = ""
                data['email_status']                = ""
                data['designation_status']          = ""
                data['emirate_id_status']           = ""
                data['foodwatch_business_id_status']= ""
                data['foodwatch_id_status']         = ""
                data['is_verified']                 = True
                if establishment_name is None:
                    data['establishment_name_status'] = "Establishment name is required"
                    data['is_verified']                 = False
                if trade_license_no is None:
                    data['trade_license_no_status'] = "Trade license no is required"
                    data['is_verified']                 = False
                email_serializer = AccountEmailSerializer(data = {"email" :invitee_email})
                if not email_serializer.is_valid():
                    data['email_status'] = "Email already exist/ Invalid email"
                    data['is_verified']                 = False
                designation = Designation.objects.filter(designation=designation).first()
                if designation is None:
                    data['designation_status'] = "Designation not found"
                    data['is_verified']                 = False
                if not type(foodwatch_business_id[0]) == int:
                    data['foodwatch_business_id_status'] = "Integer value only"
                    data['is_verified']               = False
                if not type(foodwatch_id[0]) == int:
                    data['foodwatch_id_status'] = "Integer value only"
                    data['is_verified']               = False
                if len(emirate_id) > 15:
                    data['emirate_id_status'] = "Invalid emirate id"
                    data['is_verified']                 = False
                if data['is_verified'] == False:
                    exist_count = exist_count + 1
                response_data.append(data)
            data = {
                "gtcc_count"  : len(datas),
                "exist_count" : exist_count,
                "gtcc_list"   : response_data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': e.args[0]},status=status.HTTP_406_NOT_ACCEPTABLE)

class ImportGTCC(APIView):

    @transaction.atomic
    def post(self, request):
        datas           = request.data
        response_data   = []
        try:
            for data in datas['received_file']:
                is_verified         = data['is_verified']
                if is_verified:
                    invitee_email               = data['Contact Person Email Id']
                    establishment_name          = data['Establishment Name']
                    trade_license_no            = data['Trade License No']
                    foodwatch_business_id       = data['FoodWatch Business Id'],
                    foodwatch_id                = data['FoodWatch Id'],
                    first_name_temp, last_name_temp = name_maker(data['Contact Person'])
                    designation                     = Designation.objects.filter(designation=data['Designation']).first()
                    gtcc = GTCC.objects.create(
                            establishment_name      = establishment_name,
                            trade_license_no        = trade_license_no,
                            trade_license_name      = data['Establishment Name'],
                            foodwatch_business_id   = foodwatch_business_id[0],
                            foodwatch_id            = foodwatch_id[0],
                            env_sap_id              = data['GTCC Sap Id'],
                            location                = data['Location'],
                            office_email            = data['Office Email Id'],
                            po_box                  = data['PO Box'],
                            phone_no                = data['Company Contact No'],
                            created_by              = request.user
                        )
                    active_contact_person = Account.objects.create(
                        email               =   invitee_email,
                        username            =   invitee_email,
                        first_name          =   first_name_temp,
                        last_name           =   last_name_temp,
                        contact_number      =   data['Contact Number'],
                        emirate             =   data['Emirate Id'],
                        designation         =   designation,
                        inviter             =   request.user,
                        link_id             =   gtcc.id,
                        link_class          =   'GTCC',
                        user_class          =   'GTCC',
                        user_type           =   'User',
                        inviting_key        =   get_random_string(64).lower(),
                        invite_expiry_date  =   (timezone.now() + datetime.timedelta(3)),
                    )
                    gtcc.active_contact_person = active_contact_person
                    gtcc.save()
                    response_data.append(gtcc)
                    
            return Response(GTCCListSerializer(response_data, many=True).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': e.args[0]},status=status.HTTP_406_NOT_ACCEPTABLE)

class GTCCDropdownList(APIView):
    def get(self, request):
        data = GTCC.objects.all().order_by('establishment_name')
        serializer = GTCCDropdownListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PaymentList(APIView):

    def get(self, request):
        data = PaymentDetail.objects.exclude(status="Deleted")
        serializer = PaymentListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = PaymentPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(PaymentListSerializer(data).data, status=status.HTTP_200_OK)

class PaymentDetails(APIView):
    def get_object(self, pk):
        try:
            return PaymentDetail.objects.get(pk=pk)
        except PaymentDetail.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = PaymentListSerializer(data)
        return Response(serializer.data)
    
    @transaction.atomic
    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = PaymentPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(PaymentListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleList(APIView):

    def get(self, request):
        data = VehicleDetail.objects.exclude(status="Deleted")
        serializer = VehicleListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = VehiclePostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(VehicleListSerializer(data).data, status=status.HTTP_200_OK)

class VehicleDetails(APIView):
    def get_object(self, pk):
        try:
            return VehicleDetail.objects.get(pk=pk)
        except VehicleDetail.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = VehicleListSerializer(data)
        return Response(serializer.data)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = VehiclePostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(VehicleListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DriverList(APIView):

    def get(self, request):
        data = Account.objects.filter(user_class='GTCC', user_type='Driver').exclude(user_status="Deleted")
        serializer = UserLimitedDetailSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = DriverPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(DriverListSerializer(data).data, status=status.HTTP_200_OK)

class DriverDetails(APIView):
    def get_object(self, pk):
        try:
            return Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = DriverListSerializer(data)
        return Response(serializer.data)

    @transaction.atomic
    def put(self, request, pk):
        data = self.get_object(pk)
        serializer = DriverPostSerializer(data, data=request.data)
        if serializer.is_valid():
            data = serializer.save(modified_by = request.user)
            return Response(DriverListSerializer(data).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleQRCodeScan(APIView):
    permission_classes = [IsAuthenticated, IsDriver]
    @transaction.atomic
    def post(self, request):
        data = request.data
        random_key = data['random_key']
        driver = request.user
        vehicle = VehicleDetail.objects.filter(random_key=random_key).exclude(status='Deleted').first()
        if not vehicle:
            return Response("Invalid QR Code !", status=status.HTTP_404_NOT_FOUND)
        if(driver.link_id != vehicle.gtcc.id):
            return Response("Unauthorized !", status=status.HTTP_403_FORBIDDEN)
        # Request type can be "qr_checking" or "qr_confirming"
        # qr_checking will be to check the qr code of the vehicle for the driver.
        # qr_confirming will update the database
        request_type = data['request_type']
        if (request_type == 'qr_confirming'):
            if vehicle.driver is not None:
                return Response("Vehicle already in use", status=status.HTTP_403_FORBIDDEN)
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
        serialized_data = VehicleListSerializer(vehicle).data
        waste_collected_but_not_dumped= ServiceRequest.objects.filter(vehicle = 1, status='Completed').aggregate(Sum('total_gallon_collected'))['total_gallon_collected__sum']
        try:
            serialized_data['collected_waste'] = str(round(waste_collected_but_not_dumped,2))
        except:
            serialized_data['collected_waste'] = '0.00'
        return Response(serialized_data, status=status.HTTP_200_OK)

def unlink_vehicle_from_driver(driver):
    vehicle = driver.assigned_vehicle
    response = {
        'status' : False,
        'message' : "Unlink failed"
    }
    if vehicle == None:
        response['message'] = "Vehicle not found"
        return response
    else:
        service_processing_count = ServiceRequest.objects.filter(vehicle=vehicle, driver=driver, status='Processing').count()
        if service_processing_count != 0:
            response['message'] = "There is some processing jobs found"
            return response
        vehicle_entry_status     = VehicleEntryDetails.objects.filter(vehicle=vehicle, driver=driver, current_status='Entered').count()
        if vehicle_entry_status > 0:
            response['message'] = "Cannot unlink vehicle while inside the plant"
            return response
        service_requests = ServiceRequest.objects.filter(vehicle=vehicle, driver=driver, status='Assigned')
        if len(service_requests) != 0:
            for service_request in service_requests:
                ServiceRequestLog.objects.create(
                    service_request = service_request,
                    vehicle = vehicle,
                    driver = driver,
                    type = "Driver Unassigned",
                    log = f"Driver Mr.({driver.full_name}) is unassigned",
                    created_by = driver
                )
                service_request.driver = None
                service_request.save()
        driver.assigned_vehicle = None
        driver.save()
        vehicle.driver = None
        vehicle.save()
        response['status']  = True
        response['message'] = "Vehicle not found"
        return response

class UnlinkVehicleFromDriver(APIView):
    def post(self, request):
        response = unlink_vehicle_from_driver(request.user)
        if response['status']:
            return Response("Vehicle removed successfully", status=status.HTTP_200_OK)
        else:
            return Response(response['message'], status=status.HTTP_405_METHOD_NOT_ALLOWED)

class VehicleQRCodeCheck(APIView):
    # This view is for checking whether the QRcode saved in mobile storage is linked to an active vehicle or not
    # This is usefull when a driver quit the app and reload it.
    def post(self, request):
        serializer = VehicleQRCodeScanSerializer(data=request.data)
        if serializer.is_valid():
            random_key = serializer.data['random_key']
            vehicle = VehicleDetail.objects.filter(random_key=random_key).exclude(status='Deleted').first()
            if not vehicle:
                return Response("Vehicle not found", status=status.HTTP_200_OK)
            if vehicle.driver != request.user:
                return Response("Unauthorized", status=status.HTTP_200_OK)
            else:
                return Response(VehicleListSerializer(vehicle).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

class AssignVehicleToServiceRequest(APIView):

    @transaction.atomic
    def post(self, request):
        serializer = AssignVehicleForServiceRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(modified_by = request.user)
            return Response(ServiceRequestListSerializer(data).data)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

class GTCCVehicleList(APIView):

    def get(self, request, gtcc_id):
        try:
            gtcc = GTCC.objects.get(pk=gtcc_id)
        except GTCC.DoesNotExist:
            raise Http404
        data = VehicleDetail.objects.filter(gtcc = gtcc)
        return Response(VehicleLimitedListSerializer(data, many=True).data, status=status.HTTP_200_OK)

class DriverServiceRequestCount(APIView):

    def get(self, request):
        driver = request.user
        assigned_vehicle = driver.assigned_vehicle
        if assigned_vehicle == None:
            return Response('No vehicle associated with this driver',status=status.HTTP_404_NOT_FOUND)
        data = ServiceRequest.objects.filter(vehicle = assigned_vehicle)
        assigned_count = data.filter(status = 'Assigned').count()
        processing_count = data.filter(status = 'Processing').count()
        completed_count = data.filter(status = 'Completed').count()
        partially_completed_count = data.filter(status = 'PartiallyCompleted').count()
        context = {
            "assigned_count" : assigned_count,
            "processing_count" : processing_count,
            "completed_count" : completed_count,
            "partially_completed_count" : partially_completed_count,
        }
        return Response(context, status=status.HTTP_200_OK)

class DriverServiceRequestDetails(APIView):
    permission_classes = [IsAuthenticated, IsDriver]
    def get(self, request):
        driver = request.user
        assigned_vehicle = driver.assigned_vehicle
        # if (request.user.user_type != 'Driver'):
        #     return Response('The requested user is not a Driver !',status=status.HTTP_404_NOT_FOUND)
        if assigned_vehicle == None:
            return Response('No vehicle associated with this driver',status=status.HTTP_404_NOT_FOUND)
        
        data = allJobs_list_for_driver(assigned_vehicle.id)
        return Response(data, status=status.HTTP_200_OK)

class OperatorServiceRequestDetails(APIView):
    def get(self, request, vehicle_entry_details_id):
        data = allJobs_list_of_driver_for_operator(vehicle_entry_details_id)
        return Response(data, status=status.HTTP_200_OK)


class GTCCServiceRequestDetails(generics.ListAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    fields          = [
                        'id',
                        'foodwatch_srid',
                        'entity__establishment_name',
                        'entity__area__area',
                        'entity__zone__zone_name',
                        'grease_trap_count',
                        'total_gallon_collected',
                        'vehicle__vehicle_no',
                        'dumping_vehicledetails__txn_id',
                        'created_date__date',
                        'status'
                        ]
    search_fields   = fields
    ordering_fields = fields
    serializer_class = ServiceRequestListSerializer
     
    def get_queryset(self):
        user_class = self.request.user.user_class
        if user_class == 'GTCC':
            gtcc_id = self.request.user.link_id
            queryset = ServiceRequest.objects.filter(entity_gtcc__gtcc_id = gtcc_id).select_related('entity', 'entity_gtcc', 'vehicle', 'driver')
        elif user_class == 'Envirol':
            queryset = ServiceRequest.objects.all().select_related('entity', 'entity_gtcc', 'vehicle', 'driver').order_by('-id')
        else:
            queryset = False
        if queryset:
            id = self.request.query_params.get('id')
            if id is not None and is_int(id):
                queryset = queryset.filter(id=id)
            foodwatch_srid = self.request.query_params.get('foodwatch_srid')
            if foodwatch_srid is not None:
                queryset = queryset.filter(foodwatch_srid=foodwatch_srid)
            entity__establishment_name = self.request.query_params.get('entity__establishment_name')
            if entity__establishment_name is not None:
                queryset = queryset.filter(entity__establishment_name__icontains=entity__establishment_name)
            entity__area__area = self.request.query_params.get('entity__area__area')
            if entity__area__area is not None:
                queryset = queryset.filter(entity__area__area__icontains=entity__area__area)
            entity__zone__zone_name = self.request.query_params.get('entity__zone__zone_name')
            if entity__zone__zone_name is not None:
                queryset = queryset.filter(entity__zone__zone_name__icontains=entity__zone__zone_name)
            grease_trap_count = self.request.query_params.get('grease_trap_count')
            if grease_trap_count is not None and is_int(grease_trap_count):
                queryset = queryset.filter(grease_trap_count=grease_trap_count)
            total_gallon_collected = self.request.query_params.get('total_gallon_collected')
            if total_gallon_collected is not None:
                queryset = queryset.filter(total_gallon_collected=total_gallon_collected)
            vehicle__vehicle_no = self.request.query_params.get('vehicle__vehicle_no')
            if vehicle__vehicle_no is not None:
                queryset = queryset.filter(vehicle__vehicle_no__icontains=vehicle__vehicle_no)
            dumping_vehicledetails__txn_id = self.request.query_params.get('dumping_vehicledetails__txn_id')
            if dumping_vehicledetails__txn_id is not None:
                queryset = queryset.filter(dumping_vehicledetails__txn_id=dumping_vehicledetails__txn_id)
            created_date__date = self.request.query_params.get('created_date__date')
            if created_date__date is not None:
                queryset = queryset.filter(created_date__date=created_date__date)
            status = self.request.query_params.get('status')
            if status is not None:
                queryset = queryset.filter(status=status)
            start_date  = self.request.query_params.get('start_date')
            end_date    = self.request.query_params.get('end_date')
            if start_date != None and end_date != None:
                queryset = queryset.filter(created_date__date__gte=start_date, created_date__date__lte=end_date)
        return queryset

    def get_df(self):
        self.pagination_class = None
        records = self.filter_queryset(self.get_queryset())
        df_records = pd.DataFrame.from_records(records.values_list(*self.fields))
        columns_records  = [
                                'SR No',
                                'Foodwatch Ref', 
                                'Restaurant Name',
                                'Area', 
                                'Zone', 
                                'No.of Traps', 
                                'Total Gallon Collected',
                                'Assigned Vehicle',
                                'Discharge TXN',
                                'Created Date',
                                'Status',
                            ]
        df_records.set_axis(columns_records, axis=1, inplace=True)
        return df_records

    def get(self, request):
        pdf_download = request.GET.get('pdf_download')
        csv_download = request.GET.get('csv_download')
        if (csv_download != None):
            df = self.get_df()
            df.set_index('SR No', inplace=True)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=file.csv'
            df.to_csv(path_or_buf=response)
            return response
        elif (pdf_download != None):
            df = self.get_df()
            header = {
                'SR No' : 'SR No',
                'Foodwatch Ref' : 'Foodwatch Ref',
                'Restaurant Name' : 'Restaurant Name',
                'Area' : 'Area',
                'Zone' : 'Zone',
                'No.of Traps' : 'No.of Traps',
                'Total Gallon Collected' : 'Total Gallon Collected',
                'Assigned Vehicle' : 'Assigned Vehicle',
                'Discharge TXN' : 'Discharge TXN',
                'Created Date' : 'Created Date',
                'Status' : 'Status',
            }
            data = {
                "header" : header,
                "body" : df.to_dict(orient='records'),
            }
            return Response(data, status=status.HTTP_200_OK)
        return super(GTCCServiceRequestDetails, self).get(request)

class ServiceRequestGreaseTraps(APIView):

    def get(self, request, service_request_id):
        try:
            service_request = ServiceRequest.objects.get(pk=service_request_id)
        except ServiceRequest.DoesNotExist:
            raise Http404
        data = ServiceRequestDetail.objects.filter(service_request = service_request)
        return Response(ServiceRequestDetailListSerializer(data, many=True).data, status=status.HTTP_200_OK)


def service_request_details_for_mobile_creator(service_request_id):
    service_request = ServiceRequest.objects.get(pk=service_request_id)
    entity = service_request.entity
    entity_contact = service_request.entity.active_contact_person
    service_request_serialized = ServiceRequestSerializer(service_request).data
    greaseTraps = ServiceRequestDetail.objects.filter(service_request = service_request)
    greaseTraps_serialized = ServiceRequestDetailListSerializer(greaseTraps, many=True).data
    service_request_serialized['restaurant'] = EntitySerializer(entity).data
    service_request_serialized['restaurantContact'] = UserLimitedDetailSerializer(entity_contact).data
    service_request_serialized['greaseTraps'] = ServiceRequestDetailListSerializer(greaseTraps, many=True).data
    logs = ServiceRequestLog.objects.filter(service_request_id = service_request_id).order_by('created_date')
    log_array = []
    for log in logs:
        item = { 'time': log.created_date.strftime("%m/%d/%Y - %H:%M:%S"), 'title': log.type, 'description': log.log}
        log_array.append(item)
    service_request_serialized['logs'] = log_array
    return service_request_serialized


class ServiceRequestGreaseTrapsForMobileApp(APIView):
    def get(self, request, service_request_id):
        try:
            service_request_serialized = service_request_details_for_mobile_creator(service_request_id)
            return Response(service_request_serialized, status=status.HTTP_200_OK)
        except ServiceRequest.DoesNotExist:
            raise Http404

# class UpdateServiceRequestDetails(APIView):

#     def post(self, request):
#         service_request = request.data.get('service_request', None)
#         grease_traps    = request.data.get('grease_traps', [])
#         if service_request and len(grease_traps) > 0:
#             try:
#                 service_request = ServiceRequest.objects.get(pk=service_request)
#             except ServiceRequest.DoesNotExist:
#                 raise Http404
#             for grease_trap in grease_traps:
#                 grease_trap_detail = ServiceRequestDetail.objects.get(pk=grease_trap['id'])
#                 if grease_trap_detail.status == 'Pending':
#                     grease_trap_detail.grease_trap_condtion = grease_trap['grease_trap_condtion']
#                     grease_trap_detail.waste_contents = grease_trap['waste_contents']
#                     grease_trap_detail.cover_condition = grease_trap['cover_condition']
#                     grease_trap_detail.buffle_wall_condition = grease_trap['buffle_wall_condition']
#                     grease_trap_detail.outlet_elbow_condition = grease_trap['outlet_elbow_condition']
#                     grease_trap_detail.status = grease_trap['status']
#                     grease_trap_detail.modified_by = request.user
#                     grease_trap_detail.save()
#             return Response(grease_traps, status=status.HTTP_200_OK)
#         else:
#            return Response("Service request and Grease traps are required", status=status.HTTP_406_NOT_ACCEPTABLE) 

def allJobs_list_for_driver(vehicleId):
    data = ServiceRequest.objects.filter(vehicle_id = vehicleId).exclude(status='Discharged').exclude(status='Canceled')
    serialized_data = ServiceRequestSerializer(data,many=True).data
    return serialized_data

def allJobs_list_of_driver_for_operator(vehicle_entry_details_id):
    srs = ServiceRequest.objects.filter(dumping_vehicledetails_id = vehicle_entry_details_id)
    coupons = Coupon.objects.filter(dumping_vehicledetails_id = vehicle_entry_details_id)
    serialized_srs = ServiceRequestSerializer(srs,many=True).data
    serialized_coupons = CouponListSerializerLimited(coupons,many=True).data
    data = {
                'srs':serialized_srs,
                'coupons':serialized_coupons,
            }
    return data

class UpdateServiceRequest(APIView):
    def post(self, request):
        service_request_id = request.data.get('id', None)
        if service_request_id == None:
            raise Http404
        else:
            service_request = ServiceRequest.objects.get(pk = service_request_id)
            if service_request.status != "Processing":
                return Response("You cannot modify this service request", status=status.HTTP_304_NOT_MODIFIED)

            service_request.status = "Completed"
            service_request.publish_location = request.data.get('publish_location', None)
            service_request.collection_completion_time = timezone.now()
            service_request.modified_by = request.user
            service_request.save()

            driver = service_request.driver
            entity = service_request.entity

            ServiceRequestLog.objects.create(
                service_request = service_request,
                vehicle = service_request.vehicle,
                driver = driver,
                type = "Job Completed",
                log = f"This job has been completed by Mr.{driver.full_name} at the {entity.establishment_name} restaurant",
                created_by = driver
            )

            data = allJobs_list_for_driver(service_request.vehicle.id)
            return Response(data, status=status.HTTP_200_OK)

class UpdateServiceRequestGreaseTrapDetails(APIView):
    def post(self, request):
        service_request_detail_id = request.data.get('id', None)
        service_request_detail_status = request.data.get('status', 'Pending')
        if service_request_detail_id == None:
            raise Http404
        else:
            service_request_detail = ServiceRequestDetail.objects.get(pk = service_request_detail_id)
            service_request_detail.modified_by = request.user
            service_request_detail.grease_trap_condtion = request.data.get('grease_trap_condtion', 'Not set')
            service_request_detail.waste_contents = request.data.get('waste_contents', 'Not set')
            service_request_detail.cover_condition = request.data.get('cover_condition', 'Not set')
            service_request_detail.buffle_wall_condition = request.data.get('buffle_wall_condition', 'Not set')
            service_request_detail.outlet_elbow_condition = request.data.get('outlet_elbow_condition', 'Not set')
            service_request_detail.status = service_request_detail_status
            service_request_detail.save()

            if service_request_detail_status != 'Skipped':
                service_request = service_request_detail.service_request

                service_request.total_gallon_collected += service_request_detail.grease_trap.capacity
                service_request.save()

            beforePicsNew_array = request.data.getlist('beforePicsNew',[])
            beforePicsUntouched_array = request.data.getlist('beforePicsUntouched',[])
            afterPicsNew_array = request.data.getlist('afterPicsNew',[])
            afterPicsUntouched_array = request.data.getlist('afterPicsUntouched',[])

            existing_before_images = ServiceRequestDetailImage.objects.filter(service_request_detail = service_request_detail, image_type = 'Before')
            existing_after_images = ServiceRequestDetailImage.objects.filter(service_request_detail = service_request_detail, image_type = 'After')
            existing_before_images_ids = [str(x.id) for x in existing_before_images]
            existing_after_images_ids = [str(x.id) for x in existing_after_images]
            for image in beforePicsNew_array:
                obj = ServiceRequestDetailImage.objects.create(
                    service_request_detail = service_request_detail,
                    image_type = 'Before',
                    uploaded_by = request.user)
                obj.image.save(image.name,image,save=False)
                obj.save()
            for image in afterPicsNew_array:
                obj = ServiceRequestDetailImage.objects.create(
                    service_request_detail = service_request_detail,
                    image_type = 'After',
                    uploaded_by = request.user)
                obj.image.save(image.name,image,save=False)
                obj.save()
            for itemId in existing_before_images_ids:
                if (itemId in beforePicsUntouched_array):
                    pass
                else:
                    ServiceRequestDetailImage.objects.get(pk=int(itemId)).delete()
            for itemId in existing_after_images_ids:
                if (itemId in afterPicsUntouched_array):
                    pass
                else:
                    ServiceRequestDetailImage.objects.get(pk=int(itemId)).delete()
                    
            # driver_data = Account.objects.filter(pk = request.user.id, user_class='GTCC', user_type='Driver').exclude(user_status="Deleted").first()
            # if driver_data is None:
            #     return Response("Driver not found", status=status.HTTP_404_NOT_FOUND)
            # data = ServiceRequest.objects.filter(driver = request.user)
            data = service_request_details_for_mobile_creator(service_request_detail.service_request.id)
            return Response(data, status=status.HTTP_200_OK)

class GTCCAndDriversList(APIView):
    def get(self, request):
        data = GTCC.objects.exclude(status="Deleted").order_by('establishment_name')
        serializer = GTCCAndDriversListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BookletList(APIView):

    def get(self, request, active = False):
        if active:
            data = Booklet.objects.filter(status="Active")
        else:
            data = Booklet.objects.exclude(status="Deleted")
        serializer = BookletListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BookletPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(BookletListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookletDetails(APIView):

    def get_object(self, pk):
        try:
            return Booklet.objects.get(pk=pk)
        except Booklet.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = BookletListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = BookletPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            if data.status == 'Issued':
                response = {'response':"You cannot modify this booklet", 'status':'error'}
                return Response(response, status=status.HTTP_403_FORBIDDEN)
            serializer.save(modified_by = request.user)
            return Response(BookletListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CouponBookletList(APIView):

    def get(self, request):
        data = CouponBooklet.objects.exclude(status="Deleted")
        serializer = CouponBookletListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = CouponBookletPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(CouponBookletListSerializer(data).data, status=status.HTTP_200_OK)

class CouponBookletDetails(APIView):
    def get_object(self, pk):
        try:
            return CouponBooklet.objects.get(pk=pk)
        except CouponBooklet.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = CouponBookletListSerializer(data)
        return Response(serializer.data)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = CouponBookletPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(CouponBookletListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CouponList(APIView):

    def get(self, request):
        booklet_id          = self.request.query_params.get('booklet_id')
        coupon_status_list  = self.request.query_params.getlist('coupon_status', None)
        coupon = Coupon.objects.filter(booklet=booklet_id)
        if coupon_status_list != None:
            coupon = coupon.filter(status__in = coupon_status_list)
        serializer = CouponListSerializer(coupon, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GTCCCouponBooklet(APIView):

    def get(self, request):
        gtcc = request.user.link_id
        data = CouponBooklet.objects.filter(gtcc_id=gtcc)
        serializer = CouponBookletListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GTCCUsedCouponList(APIView):

    def get(self, request):
        gtcc = request.user.link_id
        data = Coupon.objects.filter(booklet__gtcc_id=gtcc, status='Used')
        serializer = CouponListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddDeleteCouponView(APIView):
    permission_classes = [IsAuthenticated, IsOperator]
    @transaction.atomic
    def post(self, request,pk):
        data = request.data
        coupon_no = int(data['coupon_no'])
        coupon = Coupon.objects.filter(coupon_no=coupon_no)
        if (len(coupon) == 0):
            response = {'response':"Invalid Coupon", 'status':'error'}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        coupon = coupon[0]
        if(coupon.status == 'Converted' or coupon.status == 'Used'):
            response = {'response':"This coupon has already been used!", 'status':'error'}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        try:
            vehicle_entry_details = VehicleEntryDetails.objects.filter(id=data['vehicle_id'],current_status='Entered').last()
            if(coupon.booklet.gtcc.id != vehicle_entry_details.gtcc.id):
                response = {'response':"This coupon is not belongs to this GTCC!", 'status':'error'}
                return Response(response, status=status.HTTP_403_FORBIDDEN)
            if(coupon.booklet.vehicle.id != vehicle_entry_details.vehicle.id):
                response = {'response':"This coupon is not belongs to this Vehicle!", 'status':'error'}
                return Response(response, status=status.HTTP_403_FORBIDDEN)
            coupon.total_gallons = int(data['total_gallons'])
            coupon.returned_on = timezone.now()
            coupon.returned_by_id = int(data['driver_id'])
            coupon.collected_by = request.user
            coupon_image = data['coupon_image']
            coupon.image.save(coupon_image.name,coupon_image,save=False)
            coupon.vehicle = vehicle_entry_details.vehicle
            coupon.dumping_vehicledetails = vehicle_entry_details
            coupon.status = 'Used'
            coupon.save()
            vehicle_entry_details.total_gallon_collected += int(data['total_gallons'])
            vehicle_entry_details.save()
            booklet = coupon.booklet
            booklet.used_coupons += 1
            booklet.save()
            coupons = Coupon.objects.filter(dumping_vehicledetails = vehicle_entry_details)
            serialized = CouponListSerializerLimited(coupons, many=True).data
            response = {'response':"Coupon has been saved successfully !", 'status':'success', 'data':serialized}
            return Response(response, status=status.HTTP_200_OK)
        except:
            response = {'response':"Invalid details provided", 'status':'error'}
            return Response(response, status=status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    def delete(self, resquest,pk):
        coupon = Coupon.objects.filter(id=pk)
        if (len(coupon) == 0):
            response = {'response':"Invalid Coupon", 'status':'error'}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        coupon = coupon[0]
        if(coupon.status != 'Converted'):
            response = {'response':"Invalid Action!", 'status':'error'}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        try:
            vehicle_entry_details = coupon.dumping_vehicledetails
            coupon_total_gallons = coupon.total_gallons
            coupon.total_gallons = None
            coupon.converted_on = None
            coupon.converted_by = None
            coupon.collected_by = None
            coupon.status = 'Issued'
            coupon.image = None
            coupon.vehicle = None
            coupon.dumping_vehicledetails = None
            coupon.save()
            booklet = coupon.booklet
            booklet.used_coupons -= 1
            booklet.save()
            vehicle_entry_details.total_gallon_collected -= coupon_total_gallons
            vehicle_entry_details.save()
            coupons = Coupon.objects.filter(dumping_vehicledetails = vehicle_entry_details)
            serialized = CouponListSerializerLimited(coupons, many=True).data
            response = {'response':"Coupon has been deleted successfully !", 'status':'success', 'data':serialized}
            return Response(response, status=status.HTTP_200_OK)
        except:
            response = {'response':"Invalid details provided", 'status':'error'}
            return Response(response, status=status.HTTP_403_FORBIDDEN)



def vehicle_list_for_operator():
    vehicles = VehicleEntryDetails.objects.filter(entry_time__date=timezone.now().date()) | VehicleEntryDetails.objects.filter(current_status='Entered')
    serialized_data = VehicleEntryDetailsSerializer(vehicles, many=True).data
    return serialized_data



class VehicleListForOperatorView(APIView):
    permission_classes = [IsAuthenticated, IsOperator]
    def get(self,request):
        data = vehicle_list_for_operator()
        return Response(data, status=status.HTTP_200_OK)

class RFIDDetectionForVehicle(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        rfid = request.data.get('rfid', None)
        if rfid == None:
            return Response("RFID is required", status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                rfid_Card = RFIDCard.objects.get(tag_id=rfid)
                vehicle = rfid_Card.vehicle
                driver  = vehicle.driver
                gtcc    = vehicle.gtcc
                if vehicle == None:
                    return Response("No vehicle tagged with this RFID", status=status.HTTP_404_NOT_FOUND)
                if vehicle.status != "Active":
                    return Response("Vehicle not found", status=status.HTTP_404_NOT_FOUND)
                if driver == None:
                    return Response("No driver is associated with this vehicle", status=status.HTTP_404_NOT_FOUND)
                if gtcc.status != "Active":
                    return Response("GTCC not found", status=status.HTTP_404_NOT_FOUND)
                if gtcc.credit_available <=0:
                    return Response("Credit not available", status=status.HTTP_406_NOT_ACCEPTABLE)
                vehicle_entry_list = VehicleEntryDetails.objects.filter(vehicle = vehicle, current_status = 'Entered')   
                if len(vehicle_entry_list) != 0:
                    return Response("Vehicle already entered", status=status.HTTP_406_NOT_ACCEPTABLE)
                srs_processing = ServiceRequest.objects.filter(vehicle=vehicle, status='Processing')
                if len(srs_processing) != 0:
                    return Response("There is processing jobs found. Complete jobs before entering yard", status=status.HTTP_406_NOT_ACCEPTABLE)
                srs_completed = ServiceRequest.objects.filter(vehicle=vehicle, status='Completed')
                if len(srs_completed) == 0:
                    return Response("There is no completed service request found", status=status.HTTP_406_NOT_ACCEPTABLE)
                total_waste_collected = srs_completed.aggregate(Sum('total_gallon_collected'))['total_gallon_collected__sum']
                vehicle_entry_details = VehicleEntryDetails.objects.create(
                                        vehicle = vehicle,
                                        driver = driver,
                                        total_gallon_collected = total_waste_collected,
                                        gtcc = gtcc,
                                        entry_time = timezone.now(),
                                        current_status = 'Entered'
                                    )
                for sr_completed in srs_completed:
                    sr_completed.dumping_vehicledetails = vehicle_entry_details
                    sr_completed.save()
                return Response("Vehicle entered", status=status.HTTP_200_OK)
            except RFIDCard.DoesNotExist:
                return Response("RFID details not found", status=status.HTTP_404_NOT_FOUND)      

def vehicle_details_for_operator_maker(vehicle_id):
    vehicle = VehicleDetail.objects.get(id = vehicle_id)
    serialized_data = VehicleListSerializer(vehicle).data
    return serialized_data

class VehicleDetailsForOperatorView(APIView):
    def get(self, request, pk):
        vehicle_entry_details_id = pk
        try:
            vehicle_entry_details = VehicleEntryDetails.objects.get(pk=vehicle_entry_details_id)
        except:
            raise Http404
        jobs = allJobs_list_of_driver_for_operator(vehicle_entry_details.id)
        vehicle_details = VehicleEntryDetailsSerializer(vehicle_entry_details).data
        gtcc_credit = vehicle_entry_details.gtcc.credit_available
        data = {
            'vehicle_details' : vehicle_details,
            'jobs' : jobs,
            'gtcc_credit':gtcc_credit,
            'vehicle_entry_time':vehicle_entry_details.entry_time,
            }
        return Response(data, status=status.HTTP_200_OK)



class VehicleQRCodeScanForOperator(APIView):
    def post(self, request):
        random_key = request.data['random_key']
        try:
            vehicle = VehicleDetail.objects.get(random_key=random_key)
            serialized_data = VehicleListSerializer(vehicle).data
            return Response(serialized_data, status=status.HTTP_200_OK)
        except:
            return Response({'error' : 'Invaid QR Code'}, status=status.HTTP_400_BAD_REQUEST)


# TODO - this is temporary, needs to remove. 
class RFIDDetectionForVehicleTemp(APIView):
    permission_classes = [AllowAny]
    def get(self, request, rfid):
        if rfid == None:
            raise Http404
        else:
            try:
                rfid_Card = RFIDCard.objects.get(tag_id=rfid)
            except RFIDCard.DoesNotExist:
                raise Http404
            vehicle = rfid_Card.vehicle
            if vehicle == None:
                return Response("No vehicle tagged with this RFID", status=status.HTTP_404_NOT_FOUND)
            else:
                if vehicle.status != "Active":
                    return Response("Vehicle not found", status=status.HTTP_404_NOT_FOUND)
                elif vehicle.envirol_entry_status == "Entered":
                    return Response("Vehicle already entered", status=status.HTTP_406_NOT_ACCEPTABLE)
                else:
                    gtcc = vehicle.gtcc
                    if gtcc.status != "Active":
                        return Response("GTCC not found", status=status.HTTP_404_NOT_FOUND)
                    elif gtcc.credit_available <=0:
                        return Response("Credit not available", status=status.HTTP_406_NOT_ACCEPTABLE)
                    else:
                        vehicle.envirol_entry_status = 'Entered'
                        vehicle.save()
                        return Response("Vehicle entry status updated", status=status.HTTP_200_OK)

class GTCCContractList(generics.ListAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields =     [
                        'entity__establishment_name',
                        'gtcc__establishment_name',
                        'status'
                        ]
    serializer_class = GTCCContractListSerializer
    
    def get_queryset(self):
        user   = self.request.user
        status = self.request.GET.get('status')
        if user.user_class == 'Envirol':
            records = EntityGTCC.objects.filter(status=status)
        else:
            records = EntityGTCC.objects.filter(gtcc=user.link_id, status=status)
        return records

class ApproveOrRejectEntityContract(APIView):

    def post(self, request):
        gtcc                    = request.user.link_id
        contract_id             = request.data['contract_id']
        contract_status         = request.data['contract_status']
        reason_for_rejection    = request.data.get('reason_for_rejection', None)
        if contract_id == None:
            return Response("Contract id is required", status=status.HTTP_406_NOT_ACCEPTABLE)
        if contract_status == None:
            return Response("Contract status is required", status=status.HTTP_406_NOT_ACCEPTABLE)
        if contract_status not in ['Active', 'Rejected']:
            return Response("Invalid contract status", status=status.HTTP_406_NOT_ACCEPTABLE)
        if contract_status == 'Rejected' and reason_for_rejection == None:
            return Response("Rejection reason is required", status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            contract_details = EntityGTCC.objects.get(pk=contract_id)
        except GTCC.DoesNotExist:
            raise Http404
        if contract_details.status == 'Approval Pending':
            if contract_status == "Active":
                contract_details.contract_start = datetime.date.today()
            else:
                contract_details.reason_for_rejection = reason_for_rejection
            contract_details.status = contract_status
            contract_details.save()
            serializer =  GTCCContractListSerializer(contract_details)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Only pending request can accept/reject", status=status.HTTP_406_NOT_ACCEPTABLE)

# TODO - this is temporary, needs to remove.
class VehicleStatusUpdate(APIView):
    @transaction.atomic
    def post(self, request):
        vehicle_number = request.data['vehicle_number']
        vehicle_entry_status = request.data['status']
        try:
            vehicle = VehicleDetail.objects.get(vehicle_no=vehicle_number)
            driver = vehicle.driver
            if driver == None:
                return Response({'error' : 'There is no driver assosiated with this vehicle'}, status=status.HTTP_400_BAD_REQUEST)
            service_requests = ServiceRequest.objects.filter(vehicle=vehicle, status='Completed')
            if len(service_requests) == 0:
                return Response({'error' : 'There are no completed service requests in this vehicle'}, status=status.HTTP_400_BAD_REQUEST)
            vehicle_entry_details = VehicleEntryDetails.objects.create(
                                        vehicle = vehicle,
                                        driver = driver,
                                        gtcc= vehicle.gtcc,
                                        entry_time = timezone.now(),
                                        current_status='Entered'
                                    )
            total_gallon_collected = 0
            for service_request in service_requests:
                service_request.dumping_vehicledetails = vehicle_entry_details
                service_request.save()

                total_gallon_collected += service_request.total_gallon_collected

            vehicle_entry_details.total_gallon_collected = total_gallon_collected
            vehicle_entry_details.save()

            vehicle.envirol_entry_status = vehicle_entry_status
            vehicle.save()
            return Response(vehicle_entry_status, status=status.HTTP_200_OK)
        except:
            return Response({'error' : 'Vehicle not found'}, status=status.HTTP_400_BAD_REQUEST)
        

class OperatorDumpingAcceptanceView(APIView):
    @transaction.atomic
    def post(self, request):
        data = request.data
        try:
            vehicle_entry_details = VehicleEntryDetails.objects.get(id = data['vehicle_entry_details_id'])
        except:
            return Response({'error' : 'Vehicle not found'}, status=status.HTTP_400_BAD_REQUEST)
        if (data['operator_acceptance'] == 'Accepted'):
            unit_price_model, _     = Unitprice.objects.get_or_create()
            unit_price              = unit_price_model.unit_price
            vat                     = 0.05
            total_fee_for_dumping   = float(vehicle_entry_details.total_gallon_collected) * float(unit_price) * float(1+vat)
            gtcc                    = vehicle_entry_details.gtcc

            if (total_fee_for_dumping > float(gtcc.credit_available)):
                return Response({'error' : 'Insufficient balance !'}, status=status.HTTP_400_BAD_REQUEST)

            vehicle_entry_details.total_gallon_dumped   = vehicle_entry_details.total_gallon_collected
            vehicle_entry_details.total_dumping_fee     = total_fee_for_dumping
            new_balance                                 = float(gtcc.credit_available) - float(total_fee_for_dumping)
            gtcc.credit_available                       = new_balance
            gtcc.save()

            # Now we need to update all the SRs as dumber
            srs = ServiceRequest.objects.filter(dumping_vehicledetails_id = vehicle_entry_details.id).select_related('driver')
            for sr in srs:
                driver = sr.driver

                sr.status           = 'Discharged'
                sr.discharge_time   = timezone.now()
                sr.save()

                ServiceRequestLog.objects.create(
                    service_request     = sr,
                    vehicle             = sr.vehicle,
                    driver              = driver,
                    type                = "Job Discharged",
                    log                 = f"This job has been discharged by Mr.{request.user.full_name}",
                    created_by          = request.user
                )
        vehicle_entry_details.operator              = request.user   
        vehicle_entry_details.operator_acceptance   = data['operator_acceptance']
        vehicle_entry_details.exit_time             = timezone.now()
        vehicle_entry_details.remarks               = data['remarks']
        vehicle_entry_details.current_status        = "Exited"
        vehicle_entry_details.save()
        jobs = allJobs_list_of_driver_for_operator(vehicle_entry_details.id)
        vehicle_details = VehicleEntryDetailsSerializer(vehicle_entry_details).data
        data = {
                    'vehicle_details'   : vehicle_details,
                    'jobs'              : jobs
                }
        return Response(data, status=status.HTTP_200_OK)

#Dashboard API
class WalletDetails(APIView):
    permission_classes = [IsAuthenticated, IsGTCCUser]
    
    def get_object(self, gtcc):
        try:
            return GTCC.objects.get(pk=gtcc)
        except GTCC.DoesNotExist:
            raise Http404

    def get(self, request):
        gtcc            = request.user.link_id
        gallons_divsion = decimal.Decimal(1.675)
        data            = self.get_object(gtcc)
        current_wallet_balance_in_dirhams   = data.credit_available
        current_wallet_balance_in_gallons   = current_wallet_balance_in_dirhams / gallons_divsion
        total_paid_amount                   = PaymentDetail.objects.filter(gtcc=gtcc, payment_type='Credit').aggregate(Sum('amount'))
        total_paid_amount_in_dirhams        = total_paid_amount['amount__sum']
        total_paid_amount_in_gallons        = total_paid_amount_in_dirhams / gallons_divsion
        total_discharged_amount_in_dirhams  = total_paid_amount_in_dirhams - current_wallet_balance_in_dirhams
        total_discharged_amount_in_gallons  = total_paid_amount_in_gallons - current_wallet_balance_in_gallons
        data = {
                    'current_wallet_balance_in_dirhams'     : current_wallet_balance_in_dirhams,
                    'current_wallet_balance_in_gallons'     : current_wallet_balance_in_gallons,
                    'total_paid_amount_in_dirhams'          : total_paid_amount_in_dirhams,
                    'total_paid_amount_in_gallons'          : total_paid_amount_in_gallons,
                    'total_discharged_amount_in_dirhams'    : total_discharged_amount_in_dirhams,
                    'total_discharged_amount_in_gallons'    : total_discharged_amount_in_gallons,
                }
        return Response(data, status=status.HTTP_200_OK)

class TransactionDetails(APIView):
    permission_classes = [IsAuthenticated, IsGTCCUser]

    def post(self, request):
        start_date      = request.data.get('start_date', None)
        end_date        = request.data.get('end_date', None)
        gtcc            = request.user.link_id
        last_6_month    = datetime.datetime.today() - datetime.timedelta(days=90)
        data            = PaymentDetail.objects.filter(gtcc=gtcc, created_date__gte=last_6_month)
        if start_date is not None and end_date is not None:
            data = data.filter(created_date__date__gte=start_date, created_date__date__lte=end_date)
        return Response(PaymentListSerializer(data, many=True).data)

class DumpingDetails(APIView):
    permission_classes = [IsAuthenticated, IsGTCCUser]

    def post(self, request):
        start_date  = request.data.get('start_date', None)
        end_date    = request.data.get('end_date', None)
        gtcc        = request.user.link_id
        if start_date == None or end_date == None:
            return Response({'error' : 'Start date and end date are required'}, status=status.HTTP_400_BAD_REQUEST)
        x_axis = pd.date_range(start_date, end_date,freq='MS').strftime("%Y-%b").tolist()
        query = f'''SELECT DATE_TRUNC('month', ("entity_servicerequest"."created_date")) AS "month",
                        DATE_TRUNC('year', ("entity_servicerequest"."created_date")) AS "year",
                        SUM("entity_servicerequest"."total_gallon_collected") AS "total_dumped"
                    FROM "entity_servicerequest"
                    INNER JOIN "entity_entitygtcc"
                        ON ("entity_servicerequest"."entity_gtcc_id" = "entity_entitygtcc"."id")
                    WHERE (("entity_servicerequest"."created_date")>= '{start_date}' AND ("entity_servicerequest"."created_date") <= '{end_date}' AND "entity_entitygtcc"."gtcc_id" = {gtcc} AND "entity_servicerequest"."status"='Discharged')
                    GROUP BY DATE_TRUNC('month', ("entity_servicerequest"."created_date")),
                        DATE_TRUNC('year', ("entity_servicerequest"."created_date"))'''
        cursor = connection.cursor()
        cursor.execute(query)
        datas = cursor.fetchall()
        y_axis = []
        for month in x_axis:
            for data in datas:
                sr_month = data[1].date().strftime("%Y")+"-"+data[0].date().strftime("%b")
                if month == sr_month:
                    y_axis.append(float(data[2]))
                else:
                    y_axis.append(0)
        response = {
            "x_axis": x_axis,
            "y_axis" : [
                {
                    "name" : "Total Discharged",
                    "data" : y_axis
                }
            ]
        }
        return Response(response, status=status.HTTP_200_OK)

class VehicleStatus(APIView):
    permission_classes = [IsAuthenticated, IsGTCCUser]

    def get(self, request):
        gtcc        = request.user.link_id
        vehicles    = VehicleDetail.objects.filter(gtcc_id=gtcc)
        active      = vehicles.filter(status='Active').count()
        deactive    = vehicles.filter(status='Disabled').count()
        stopped     = vehicles.filter(status='Active', driver__isnull=True).count()
        driver_assosiated   = vehicles.filter(status='Active', driver__isnull=False).count()
        cleaning_data       = ServiceRequest.objects.filter(entity_gtcc__gtcc_id=gtcc, status='Processing').annotate(cleaning_count=Count('vehicle', distinct=True)).values('cleaning_count')
        discharging         = VehicleEntryDetails.objects.filter(gtcc_id=gtcc, current_status='Entered').count()
        cleaning    = cleaning_data[0]['cleaning_count']
        moving      = driver_assosiated - cleaning - discharging
        data = {
                    'active'        : active,
                    'deactive'      : deactive,
                    'stopped'       : stopped,
                    'moving'        : moving,
                    'cleaning'      : cleaning,
                    'discharging'   : discharging,
                }
        return Response(data, status=status.HTTP_200_OK)

class DischargeTxnReport(generics.ListAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    fields   = [
                    'txn_id',
                    'gtcc__establishment_name',
                    'vehicle__vehicle_no',
                    'driver__full_name',
                    'entry_time',
                    'exit_time',
                    'total_gallon_collected',
                    'total_gallon_dumped',
                    'total_dumping_fee',
                    'operator_acceptance',
                    'remarks',
                    'current_status',
                ]
    search_fields   = fields
    ordering_fields = fields
    serializer_class = VehicleEntryDetailsSerializer

    def get_queryset(self):
        queryset = VehicleEntryDetails.objects.all().select_related('gtcc', 'vehicle', 'driver')
        txn_id = self.request.query_params.get('txn_id')
        if txn_id is not None:
            queryset = queryset.filter(txn_id__icontains=txn_id)
        total_gallon_collected = self.request.query_params.get('total_gallon_collected')
        if total_gallon_collected is not None:
            queryset = queryset.filter(total_gallon_collected=total_gallon_collected)
        total_dumping_fee = self.request.query_params.get('total_dumping_fee')
        if total_dumping_fee is not None:
            queryset = queryset.filter(total_dumping_fee=total_dumping_fee)
        total_gallon_dumped = self.request.query_params.get('total_gallon_dumped')
        if total_gallon_dumped is not None:
            queryset = queryset.filter(total_gallon_dumped=total_gallon_dumped)
        operator_acceptance = self.request.query_params.get('operator_acceptance')
        if operator_acceptance is not None:
            queryset = queryset.filter(operator_acceptance__icontains=operator_acceptance)
        remarks = self.request.query_params.get('remarks')
        if remarks is not None:
            queryset = queryset.filter(remarks__icontains=remarks)
        current_status = self.request.query_params.get('current_status')
        if current_status is not None:
            queryset = queryset.filter(current_status__icontains=current_status)
        vehicle__vehicle_no = self.request.query_params.get('vehicle__vehicle_no')
        if vehicle__vehicle_no is not None:
            queryset = queryset.filter(vehicle__vehicle_no__icontains=vehicle__vehicle_no)
        driver__full_name = self.request.query_params.get('driver__full_name')
        if driver__full_name is not None:
            queryset = queryset.filter(driver__full_name__icontains=driver__full_name)
        gtcc__establishment_name = self.request.query_params.get('gtcc__establishment_name')
        if gtcc__establishment_name is not None:
            queryset = queryset.filter(gtcc__establishment_name__icontains=gtcc__establishment_name)
        range_type  = self.request.query_params.get('range_type')
        start_date  = self.request.query_params.get('start_date')
        end_date    = self.request.query_params.get('end_date')
        if start_date != None and end_date != None:
            if range_type == 'Exit Time':
                queryset = queryset.filter(exit_time__date__gte=start_date, exit_time__date__lte=end_date)
            else:
                queryset = queryset.filter(entry_time__date__gte=start_date, entry_time__date__lte=end_date)
        return queryset

    def get_df(self):
        self.pagination_class = None
        records = self.filter_queryset(self.get_queryset())
        df_records = pd.DataFrame.from_records(records.values_list(*self.fields))
        columns_records  = [
                                'TXN Id',
                                'GTCC', 
                                'Assigned Vehicle',
                                'Driver', 
                                'Entry Time', 
                                'Exit Time', 
                                'Total Gallons Collected',
                                'Total Gallons Discharged',
                                'Total Dumping Fee',
                                'Operator Acceptance',
                                'Remarks',
                                'Vehicle Status',
                            ]
        df_records.set_axis(columns_records, axis=1, inplace=True)
        return df_records

    def get(self, request):
        pdf_download = request.GET.get('pdf_download')
        csv_download = request.GET.get('csv_download')
        if (csv_download != None):
            df = self.get_df()
            df.set_index('TXN Id', inplace=True)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=file.csv'
            df.to_csv(path_or_buf=response)
            return response
        elif (pdf_download != None):
            df = self.get_df()
            header = {
                'TXN Id' : 'TXN Id',
                'GTCC' : 'GTCC',
                'Assigned Vehicle' : 'Assigned Vehicle',
                'Driver' : 'Driver',
                'Entry Time' : 'Entry Time',
                'Exit Time' : 'Exit Time',
                'Total Gallons Collected' : 'Total Gallons Collected',
                'Total Gallons Discharged' : 'Total Gallons Discharged',
                'Total Dumping Fee' : 'Total Dumping Fee',
                'Operator Acceptance' : 'Operator Acceptance',
                'Remarks' : 'Remarks',
                'Vehicle Status' : 'Vehicle Status',
            }
            data = {
                "header" : header,
                "body" : df.to_dict(orient='records'),
            }
            return Response(data, status=status.HTTP_200_OK)
        return super(DischargeTxnReport, self).get(request)

class JobsAndCouponListBasedOnVehicleEntryDetails(APIView):
    def get(self, request, vehicle_entry_id):
        jobs    = ServiceRequest.objects.filter(dumping_vehicledetails__id=vehicle_entry_id)
        coupons = Coupon.objects.filter(dumping_vehicledetails__id=vehicle_entry_id)
        data = {
            "jobs"      : ServiceRequestListSerializer(jobs, many=True).data,
            "coupons"   : CouponListDetailedSerializer(coupons, many=True).data
        }
        return Response(data, status=status.HTTP_200_OK)

class CouponReport(generics.ListAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    fields   = [
                    'coupon_no',
                    'booklet__booklet__booklet_no',
                    'booklet__gtcc__establishment_name',
                    'vehicle__vehicle_no',
                    'total_gallons',
                    'returned_by__full_name',
                    'returned_on',
                    'collected_by__full_name',
                    'collected_remark',
                    'collection_violation',
                    'converted_on',
                    'converted_by__full_name',
                    'dumping_vehicledetails__txn_id',
                    'status',
                ]
    search_fields   = fields
    ordering_fields = fields
    serializer_class = CouponListDetailedSerializer

    def get_queryset(self):
        queryset = Coupon.objects.filter(Q(status='Used') | Q(status='Converted'))
        coupon_no = self.request.query_params.get('coupon_no')
        if coupon_no is not None:
            queryset = queryset.filter(coupon_no__icontains=coupon_no)
        booklet__booklet__booklet_no = self.request.query_params.get('booklet__booklet__booklet_no')
        if booklet__booklet__booklet_no is not None:
            queryset = queryset.filter(booklet__booklet__booklet_no__icontains=booklet__booklet__booklet_no)
        booklet__gtcc__establishment_name = self.request.query_params.get('booklet__gtcc__establishment_name')
        if booklet__gtcc__establishment_name is not None:
            queryset = queryset.filter(booklet__gtcc__establishment_name__icontains=booklet__gtcc__establishment_name)
        vehicle__vehicle_no = self.request.query_params.get('vehicle__vehicle_no')
        if vehicle__vehicle_no is not None:
            queryset = queryset.filter(vehicle__vehicle_no__icontains=vehicle__vehicle_no)
        total_gallons = self.request.query_params.get('total_gallons')
        if total_gallons is not None:
            queryset = queryset.filter(total_gallons=total_gallons)
        returned_by__full_name = self.request.query_params.get('returned_by__full_name')
        if returned_by__full_name is not None:
            queryset = queryset.filter(returned_by__full_name__icontains=returned_by__full_name)
        collected_by__full_name = self.request.query_params.get('collected_by__full_name')
        if collected_by__full_name is not None:
            queryset = queryset.filter(collected_by__full_name__icontains=collected_by__full_name)
        collected_remark = self.request.query_params.get('collected_remark')
        if collected_remark is not None:
            queryset = queryset.filter(collected_remark__icontains=collected_remark)
        collection_violation = self.request.query_params.get('collection_violation')
        if collection_violation is not None:
            queryset = queryset.filter(collection_violation=collection_violation)
        converted_by__full_name = self.request.query_params.get('converted_by__full_name')
        if converted_by__full_name is not None:
            queryset = queryset.filter(converted_by__full_name__icontains=converted_by__full_name)
        dumping_vehicledetails__txn_id = self.request.query_params.get('dumping_vehicledetails__txn_id')
        if dumping_vehicledetails__txn_id is not None:
            queryset = queryset.filter(dumping_vehicledetails__txn_id__icontains=dumping_vehicledetails__txn_id)
        status = self.request.query_params.get('status')
        if status is not None:
            queryset = queryset.filter(status=status)
        returned_start_date  = self.request.query_params.get('returned_start_date')
        returned_end_date    = self.request.query_params.get('returned_end_date')
        if returned_start_date != None and returned_end_date != None:
            queryset = queryset.filter(returned_on__date__gte=returned_start_date, returned_on__date__lte=returned_end_date)
        return queryset

    def get_df(self):
        self.pagination_class = None
        records = self.filter_queryset(self.get_queryset())
        df_records = pd.DataFrame.from_records(records.values_list(*self.fields))
        columns_records  = [
                                'Coupon No',
                                'Booklet No',
                                'Assigned GTCC',
                                'Vehicle',
                                'Total Gallons',
                                'Returned By',
                                'Returned On',
                                'Collected By',
                                'Remark',
                                'Violation',
                                'Converted On',
                                'Converted By',
                                'Txn Id', 
                                'Status',
                            ]
        df_records.set_axis(columns_records, axis=1, inplace=True)
        return df_records

    def get(self, request):
        pdf_download = request.GET.get('pdf_download')
        csv_download = request.GET.get('csv_download')
        if (csv_download != None):
            df = self.get_df()
            df.set_index('Coupon No', inplace=True)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=file.csv'
            df.to_csv(path_or_buf=response)
            return response
        elif (pdf_download != None):
            df = self.get_df()
            header = {
                'Coupon No' :'Coupon No' ,
                'Booklet No' :'Booklet No' ,
                'Assigned GTCC' :'Assigned GTCC' ,
                'Vehicle' : 'Vehicle',
                'Total Gallons': 'Total Gallons',
                'Returned By': 'Returned By',
                'Returned On': 'Returned On',
                'Collected By': 'Collected By',
                'Remark': 'Remark',
                'Violation': 'Violation',
                'Converted On':'Converted On',
                'Converted By':'Converted By',
                'Txn Id':'Txn Id', 
                'Status':'Status',
            }
            data = {
                "header" : header,
                "body" : df.to_dict(orient='records'),
            }
            return Response(data, status=status.HTTP_200_OK)
        return super(CouponReport, self).get(request)

class EditCouponGallons(APIView):
    def get_object(self, pk):
        try:
            return Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            raise Http404

    @transaction.atomic
    def put(self, request, pk):
        coupon = self.get_object(pk)
        total_gallons    = request.data.get('total_gallons', None)
        if total_gallons == None:
            return Response({'error' : 'Total gallons is required'}, status=status.HTTP_400_BAD_REQUEST)
        coupon_total_gallons = coupon.total_gallons
        if decimal.Decimal(total_gallons) == coupon_total_gallons:
            return Response(CouponListSerializerLimited(coupon).data)
        else:
            dumping_vehicledetails   = coupon.dumping_vehicledetails
            gtcc                     = dumping_vehicledetails.gtcc
            coupon_total_dumping_fee = dumping_vehicledetails.total_dumping_fee
            unit_price_model, _      = Unitprice.objects.get_or_create()
            unit_price               = unit_price_model.unit_price
            vat                      = 0.05
            total_fee_for_dumping    = round(decimal.Decimal(total_gallons) * decimal.Decimal(unit_price) * decimal.Decimal(1+vat),2)
            
            if (total_fee_for_dumping > float(gtcc.credit_available)):
                return Response({'error' : 'Insufficient balance !'}, status=status.HTTP_400_BAD_REQUEST)

            dumping_vehicledetails.total_gallon_collected = total_gallons
            dumping_vehicledetails.total_dumping_fee = total_fee_for_dumping
            dumping_vehicledetails.save()
            coupon.total_gallons = total_gallons
            coupon.save()
            EditCouponLog.objects.create(
                coupon = coupon,
                change = f'Total gallons edited from {coupon_total_gallons} gallons to {total_gallons} gallons and the corresponding dumping fee changed from {coupon_total_dumping_fee} AED to {total_fee_for_dumping} AED',
                edited_by = request.user
            )
            amount           = total_fee_for_dumping - coupon_total_dumping_fee
            if amount > 0:
                payment_type = 'Debit'
            else:
                payment_type = 'Credit'
            credit_available = gtcc.credit_available
            previous_balance = credit_available
            new_balance      = credit_available + amount
            payment_detail = PaymentDetail.objects.create(
                gtcc                = gtcc,
                mode_of_payment_id  = 2,
                amount              = abs(amount),
                previous_balance    = abs(previous_balance),
                new_balance         = abs(new_balance),
                txn_no              = f'DO #{dumping_vehicledetails.txn_id}',
                reference_no        = f'Coupon #{coupon.coupon_no}',
                payment_date        = datetime.date.today(),
                payment_type        = payment_type,
                created_by          = request.user
            )
            gtcc.credit_available = new_balance
            gtcc.save()
            return Response(CouponListSerializerLimited(coupon).data)

class EditCouponLogList(APIView):
    def get(self, request):
        notification = EditCouponLog.objects.all()
        serializer = EditCouponLogSerializer(notification, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)