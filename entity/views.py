from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status, generics, filters
from .serializers import *
from .models import ServiceRequestLog
from django.http import Http404, HttpResponse
from django.db import transaction
from gtcc.views import allJobs_list_for_driver
from gtcc.models import Coupon
from gtcc.serializers import CouponListSerializerLimited
import pandas as pd
import base64
from PIL import Image
from io import BytesIO
from django.core.files import File as Files
from rest_framework.permissions import IsAuthenticated
from abacimodules.permissions import IsEntityUser

class EntityList(generics.ListCreateAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields =     [
                        'establishment_name', 
                        'trade_license_no',
                        'env_sap_id',
                        'entity_location',
                        'active_contact_person__full_name',
                        'active_contact_person__email',
                        'status',
                        ]
    queryset = Entity.objects.exclude(status="Deleted")
    serializer_class = EntityListSerializer

    def get_df(self):
        self.pagination_class = None
        records = self.filter_queryset(self.get_queryset())
        users = Account.objects.all()
        df_records = pd.DataFrame.from_records(records.values_list( 
                                                                    'id',
                                                                    'trade_license_no', 
                                                                    'establishment_name',
                                                                    'env_sap_id', 
                                                                    'entity_location', 
                                                                    'active_contact_person_id', 
                                                                    'status', 
                                                                   ))
        columns_records  = ['Entity ID',
                    'License No', 
                    'Entity Name',
                    'Business ID', 
                    'Location', 
                    'active_contact_person_id', 
                    'Status',]
        df_records.set_axis(columns_records, axis=1, inplace=True)
        df_users = pd.DataFrame.from_records(users.filter(user_class='Entity').values_list('id','full_name', 'contact_number', 'email'))
        columns_users  = ['id',
                    'Contact Person', 
                    'Contact No',
                    'Email ID', ]
        df_users.set_axis(columns_users, axis=1, inplace=True)
        df = df_records.merge(df_users, how='inner', left_on='active_contact_person_id', right_on='id')
        df.drop(['active_contact_person_id','id'], inplace=True, axis=1)
        df.loc[:, ['Entity ID',
                    'License No', 
                    'Entity Name',
                    'Business ID', 
                    'Location', 
                    'Contact Person', 
                    'Email ID', 
                    'Contact No',
                    'Status',]]
        return df

    def get(self, request):
        pdf_download = request.GET.get('pdf_download')
        csv_download = request.GET.get('csv_download')
        if (csv_download != None):
            df = self.get_df()
            df.set_index('Entity ID', inplace=True)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=file.csv'
            df.to_csv(path_or_buf=response)
            return response
        elif (pdf_download != None):
            df = self.get_df()
            header = {
                'Entity ID'	    :	'Entity ID',
                'License No' 	:	'License No', 
                'Entity Name'	    :	'Entity Name',
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
        return super(EntityList, self).get(request)

    @transaction.atomic
    def post(self, request):
        serializer = EntityPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(EntityListSerializer(data).data, status=status.HTTP_200_OK)

class EntityDetails(APIView):
    def get_object(self, pk):
        try:
            return Entity.objects.get(pk=pk)
        except Entity.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityListSerializer(data).data
        # service_requests = ServiceRequest.objects.filter(entity=data)
        # serializer['service_requests'] = ServiceRequestListSerializer(service_requests, many=True).data
        return Response(serializer)

    @transaction.atomic
    def put(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityPostSerializer(data, data=request.data)
        if serializer.is_valid():
            data = serializer.save(modified_by = request.user)
            return Response(EntityListSerializer(data).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EntityServiceRequestListView(generics.ListAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields =     [
                        'id',
                        'entity_gtcc__gtcc__establishment_name',
                        'vehicle__vehicle_no',
                        'total_gallon_collected',
                        'grease_trap_count',
                        'status'
                        ]
    
    serializer_class = ServiceRequestListSerializer

    def get_queryset(self):
        
        queryset = ServiceRequest.objects.filter(entity_id=self.pk)
        start_date = self.request.GET.get('start_date',None)
        end_date = self.request.GET.get('end_date',None)
        if (start_date != None and end_date !=None):
            queryset = queryset.filter(sms_send_time_dategte=start_date).filter(sms_send_timedate_lte=end_date)
        return queryset

    # def get_df(self):
    #     self.pagination_class = None
    #     records = self.filter_queryset(self.get_queryset())
    #     users = Account.objects.all()
    #     df_records = pd.DataFrame.from_records(records.values_list( 
    #                                                                 'id',
    #                                                                 'trade_license_no', 
    #                                                                 'establishment_name',
    #                                                                 'env_sap_id', 
    #                                                                 'entity_location', 
    #                                                                 'active_contact_person_id', 
    #                                                                 'status', 
    #                                                                ))
    #     columns_records  = ['Entity ID',
    #                 'License No', 
    #                 'Entity Name',
    #                 'Business ID', 
    #                 'Location', 
    #                 'active_contact_person_id', 
    #                 'Status',]
    #     df_records.set_axis(columns_records, axis=1, inplace=True)
    #     df_users = pd.DataFrame.from_records(users.filter(user_class='Entity').values_list('id','full_name', 'contact_number', 'email'))
    #     columns_users  = ['id',
    #                 'Contact Person', 
    #                 'Contact No',
    #                 'Email ID', ]
    #     df_users.set_axis(columns_users, axis=1, inplace=True)
    #     df = df_records.merge(df_users, how='inner', left_on='active_contact_person_id', right_on='id')
    #     df.drop(['active_contact_person_id','id'], inplace=True, axis=1)
    #     df.loc[:, ['Entity ID',
    #                 'License No', 
    #                 'Entity Name',
    #                 'Business ID', 
    #                 'Location', 
    #                 'Contact Person', 
    #                 'Email ID', 
    #                 'Contact No',
    #                 'Status',]]
    #     return df

    def get(self, request, pk):
        #permission implemented
        user = request.user
        user_class = user.user_class
        if user_class == 'Envirol':
            self.pk = pk
        elif user_class == 'Entity':
            if pk == user.link_id:
                self.pk = pk
            else:
                return Response("Unauthorized", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("Unauthorized", status=status.HTTP_400_BAD_REQUEST)
        # pdf_download = request.GET.get('pdf_download')
        # csv_download = request.GET.get('csv_download')
        # if (csv_download != None):
        #     df = self.get_df()
        #     df.set_index('Entity ID', inplace=True)
        #     response = HttpResponse(content_type='text/csv')
        #     response['Content-Disposition'] = 'attachment; filename=file.csv'
        #     df.to_csv(path_or_buf=response)
        #     return response
        # elif (pdf_download != None):
        #     df = self.get_df()
        #     header = {
        #         'Entity ID'	    :	'Entity ID',
        #         'License No' 	:	'License No', 
        #         'Entity Name'	    :	'Entity Name',
        #         'Business ID' 	:	'Business ID', 
        #         'Location' 	    :	'Location', 
        #         'Contact Person':   'Contact Person', 
        #         'Email ID' 	    :	'Email ID', 
        #         'Contact No'	:	'Contact No',
        #         'Status'	    :	'Status'
        #     }
        #     data = {
        #         "header" : header,
        #         "body" : df.to_dict(orient='records'),
        #     }
        #     return Response(data, status=status.HTTP_200_OK)
        return super(EntityServiceRequestListView, self).get(request)

class ChangeEntityImage(APIView):
    
    def put(self, request, pk):
        image = request.data.get('image', None)
        try:
            entity =  Entity.objects.get(pk=pk)
        except Entity.DoesNotExist:
            raise Http404
        if image == None:
            entity.image.delete()
            entity.image == None
            entity.save()
            return Response("Deleted", status=status.HTTP_200_OK)
        else:
            image = image.split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image)))
            # if image.width > 200:
            #     image = image.resize((200, 200))
            image = image.convert('RGB')
            blob = BytesIO()
            image.save(blob, 'JPEG')
            image = Files(blob)
            entity.image.delete()
            entity.image.save('name.jpg', image)
            data = {
                "image" : entity.image.url
            }
            return Response(data, status=status.HTTP_200_OK)

class EntityDetailsForInspector(APIView):
    def get_object(self, pk):
        try:
            return Entity.objects.get(pk=pk)
        except Entity.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityListSerializer(data).data
        service_requests = ServiceRequest.objects.filter(entity=data)
        serializer['service_requests'] = ServiceRequestListSerializer(service_requests, many=True).data
        return Response(serializer)

    @transaction.atomic
    def put(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityPostSerializer(data, data=request.data)
        if serializer.is_valid():
            data = serializer.save(modified_by = request.user)
            return Response(EntityListSerializer(data).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EntityFixtureList(APIView):

    def get(self, request):
        data = EntityFixture.objects.exclude(status="Deleted")
        serializer =  EntityFixtureListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer =  EntityFixturePostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response( EntityFixtureListSerializer(data).data, status=status.HTTP_200_OK)

class EntityFixtureDetails(APIView):
    def get_object(self, pk):
        try:
            return EntityFixture.objects.get(pk=pk)
        except EntityFixture.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer =  EntityFixtureListSerializer(data)
        return Response(serializer.data)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer =  EntityFixturePostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response( EntityFixtureListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EntityGreaseTrapList(APIView):

    def get(self, request):
        data = EntityGreaseTrap.objects.exclude(status="Deleted")
        serializer =  EntityGreaseTrapListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer =  EntityGreaseTrapPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response( EntityGreaseTrapListSerializer(data).data, status=status.HTTP_200_OK)

class EntityGreaseTrapDetails(APIView):
    def get_object(self, pk):
        try:
            return EntityGreaseTrap.objects.get(pk=pk)
        except EntityGreaseTrap.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer =  EntityGreaseTrapListSerializer(data)
        return Response(serializer.data)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer =  EntityGreaseTrapPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response( EntityGreaseTrapListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EntityGTCCList(APIView):

    def get(self, request):
        data = EntityGTCC.objects.exclude(status="Deleted")
        serializer =  EntityGTCCListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer =  EntityGTCCPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response( EntityGTCCListSerializer(data).data, status=status.HTTP_200_OK)

class EntityGTCCDetails(APIView):
    def get_object(self, pk):
        try:
            return EntityGTCC.objects.get(pk=pk)
        except EntityGTCC.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer =  EntityGTCCListSerializer(data)
        return Response(serializer.data)

    @transaction.atomic
    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer =  EntityGTCCPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(EntityGTCCListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EntityQRCodeScan(APIView):
    
    @transaction.atomic
    def post(self, request):
        random_key          = request.data.get('random_key')
        service_request_id  = request.data.get('service_request_id', None)
        qr_scan_location    = request.data.get('qr_scan_location', None)
        vehicle             = request.user.assigned_vehicle
        driver              = request.user
        try:
            entity              = Entity.objects.get(random_key = random_key)
            service_requests    = ServiceRequest.objects.filter(entity=entity, vehicle=vehicle, status='Assigned')
            if (service_request_id != None):
                service_requests = service_requests.filter(id = service_request_id)
            if len(service_requests) == 0:
                return Response({'error': 'No service requests are Assigned !'}, status=status.HTTP_404_NOT_FOUND)
            elif len(service_requests) == 1:
                service_request_data                    = service_requests[0]
                service_request_data.driver             = driver
                service_request_data.status             = 'Processing'
                service_request_data.qr_scan_location   = qr_scan_location
                service_request_data.save()
                
                ServiceRequestLog.objects.create(
                    service_request     = service_request_data,
                    vehicle             = service_request_data.vehicle,
                    driver              = driver,
                    type                = "Job Started",
                    log                 = f"This job has been started by Mr.{driver.full_name} at the {entity.establishment_name} restaurant",
                    created_by          = driver
                )
                response_data = {
                    'selected_job' : ServiceRequestSerializer(service_request_data).data,
                    'all_jobs': allJobs_list_for_driver(service_request_data.vehicle.id)
                }

                # response_data = service_request_details_for_mobile_creator(service_requests[0].id)
                # data = ServiceRequest.objects.filter(vehicle = service_request_data.vehicle)
                # response_data['allJobs'] = ServiceRequestSerializer(data, many=True).data
                # service_request_serialized = [response_data]
                return Response([response_data], status=status.HTTP_200_OK)
            elif len(service_requests) > 1:
                return Response(ServiceRequestSerializer(service_requests, many=True).data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No service requests are Assigned !'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'Entity not found !'}, status=status.HTTP_404_NOT_FOUND)
        # else:
        #     return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

class ServiceRequestList(APIView):
    permission_classes = [IsAuthenticated, IsEntityUser]

    def get(self, request):
        data = ServiceRequest.objects.all()
        serializer =  ServiceRequestListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer =  ServiceRequestPostSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(ServiceRequestListSerializer(data).data, status=status.HTTP_200_OK)


class ManageEntityGreaseTrap(generics.ListAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    fields   = [
                    'grease_trap_label',
                    'entity__establishment_name',
                    'entity__active_gtcc_detail__gtcc__establishment_name',
                    'grease_trap__description',
                    'capacity',
                    'entity__zone__zone_name',
                    'entity__area__area',
                    'entity__subarea__sub_area',
                    'entity__category__main_category',
                    'entity__sub_category__sub_category',
                ]
    search_fields   = fields
    ordering_fields = fields
    serializer_class = EntityGreaseTrapDetailedSerializer

    def get_queryset(self):
        queryset = EntityGreaseTrap.objects.all()
        entity__establishment_name = self.request.query_params.get('entity__establishment_name')
        if entity__establishment_name is not None:
            queryset = queryset.filter(entity__establishment_name__icontains=entity__establishment_name)
        entity__active_gtcc_detail__gtcc__establishment_name = self.request.query_params.get('entity__active_gtcc_detail__gtcc__establishment_name')
        if entity__active_gtcc_detail__gtcc__establishment_name is not None:
            queryset = queryset.filter(entity__active_gtcc_detail__gtcc__establishment_name__icontains=entity__active_gtcc_detail__gtcc__establishment_name)
        grease_trap_label = self.request.query_params.get('grease_trap_label')
        if grease_trap_label is not None:
            queryset = queryset.filter(grease_trap_label__icontains=grease_trap_label)
        capacity = self.request.query_params.get('capacity')
        if capacity is not None:
            queryset = queryset.filter(capacity=capacity)
        entity__zone__zone_name = self.request.query_params.get('entity__zone__zone_name')
        if entity__zone__zone_name is not None:
            queryset = queryset.filter(entity__zone__zone_name__icontains=entity__zone__zone_name)
        entity__area__area = self.request.query_params.get('entity__area__area')
        if entity__area__area is not None:
            queryset = queryset.filter(entity__area__area__icontains=entity__area__area)
        entity__subarea__sub_area = self.request.query_params.get('entity__subarea__sub_area')
        if entity__subarea__sub_area is not None:
            queryset = queryset.filter(entity__subarea__sub_area__icontains=entity__subarea__sub_area)
        entity__category__main_category = self.request.query_params.get('entity__category__main_category')
        if entity__category__main_category is not None:
            queryset = queryset.filter(entity__category__main_category__icontains=entity__category__main_category)
        entity__sub_category__sub_category = self.request.query_params.get('entity__sub_category__sub_category')
        if entity__sub_category__sub_category is not None:
            queryset = queryset.filter(entity__sub_category__sub_category__icontains=entity__sub_category__sub_category)
        grease_trap__description = self.request.query_params.get('grease_trap__description')
        if grease_trap__description is not None:
            queryset = queryset.filter(grease_trap__description__icontains=grease_trap__description)
        return queryset

    def get_df(self):
        self.pagination_class = None
        records = self.filter_queryset(self.get_queryset())
        df_records = pd.DataFrame.from_records(records.values_list(*self.fields))
        columns_records  = [
                                'GT Label',
                                'Entity', 
                                'Active GTCC',
                                'Trap Type', 
                                'Capacity', 
                                'Zone', 
                                'Area',
                                'Sub Area',
                                'Main Category',
                                'Sub Category',
                            ]
        df_records.set_axis(columns_records, axis=1, inplace=True)
        return df_records

    def get(self, request):
        pdf_download = request.GET.get('pdf_download')
        csv_download = request.GET.get('csv_download')
        if (csv_download != None):
            df = self.get_df()
            df.set_index('GT Label', inplace=True)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=file.csv'
            df.to_csv(path_or_buf=response)
            return response
        elif (pdf_download != None):
            df = self.get_df()
            header = {
                'GT Label' : 'GT Label',
                'Entity' : 'Entity',
                'Active GTCC' : 'Active GTCC',
                'Trap Type' : 'Trap Type',
                'Capacity' : 'Capacity',
                'Zone' : 'Zone',
                'Area' : 'Area',
                'Sub Area' : 'Sub Area',
                'Main Category' : 'Main Category',
                'Sub Category' : 'Sub Category'
            }
            data = {
                "header" : header,
                "body" : df.to_dict(orient='records'),
            }
            return Response(data, status=status.HTTP_200_OK)
        return super(ManageEntityGreaseTrap, self).get(request)

class EntityWithGreaseTraps(APIView):
    def get(self, request):
        data = Entity.objects.filter(status='Active')
        return Response(EntityWithGreaseTrapsSerializer(data, many=True).data)

class ConvertCouponToSR(APIView):
    def get_coupon(self, pk):
        try:
            return Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            raise Http404

    @transaction.atomic
    def post(self, request):
        coupon_id               = request.data.get('coupon_id', None)
        total_gallons           = request.data.get('total_gallons', None)
        service_request_date    = request.data.get('service_request_date', None)
        if coupon_id == None:
            return Response({'error' : 'Coupon id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if total_gallons == None:
            return Response({'error' : 'Total gallons is required'}, status=status.HTTP_400_BAD_REQUEST)
        if service_request_date == None:
            return Response({'error' : 'Service request date is required'}, status=status.HTTP_400_BAD_REQUEST)
        coupon                  = self.get_coupon(coupon_id)
        dumping_vehicledetails  = coupon.dumping_vehicledetails
        vehicle                 = dumping_vehicledetails.vehicle
        driver                  = dumping_vehicledetails.driver
        operator                = dumping_vehicledetails.operator
        serializer =  ServiceRequestPostSerializer(
                            data                    = request.data,
                            vehicle                 = vehicle,
                            driver                  = driver,
                            operator                = operator,
                            dumping_vehicledetails  = dumping_vehicledetails,
                            created_by              = request.user,
                            collection_completion_time = service_request_date,
                            created_date                = service_request_date,
                            status                      = 'Discharged',
                            initiator                   = 'CPN',
                            sr_grease_trap_status       = 'Completed'
                        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if coupon.status != 'Used':
            return Response({'error' : 'Only used coupons can be converted'}, status=status.HTTP_400_BAD_REQUEST)
        if total_gallons != coupon.total_gallons:
            return Response({'error' : 'Selected grease trap total gallon does not match with coupon total gallon'}, status=status.HTTP_400_BAD_REQUEST)
        if service_request_date >= coupon.returned_on:
            return Response({'error' : 'Selected grease trap total gallon does not match with coupon total gallon'}, status=status.HTTP_400_BAD_REQUEST)
            
        service_request    = serializer.save(created_by = request.user)

        coupon.converted_on     = timezone.now()
        coupon.converted_by     = request.user
        coupon.service_request  = service_request
        coupon.status           = 'Converted'
        coupon.save()
        
        return Response(CouponListSerializerLimited(coupon).data, status=status.HTTP_200_OK)

class ServiceRequestLogList(APIView):
    def get(self, request, service_request_id):
        logs = ServiceRequestLog.objects.filter(service_request_id = service_request_id).order_by('created_date')
        return Response(ServiceRequestLogSerializer(logs, many=True).data)

