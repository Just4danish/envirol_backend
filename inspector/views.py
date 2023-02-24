from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status
from masters.models import Zone, Area, SubArea
from entity.models import Entity, EntityLog,ServiceRequest
from .serializers import *
from abacimodules.abacifunctions import smart_search_response_creator, get_locations_for_smart_search
from entity.serializers import ServiceRequestListSerializer, EntityListSerializer, SubAreaListSerializer
from django.db import transaction
from django.http import Http404

class ZoneList(APIView):
    def get(self, request):
        data = Zone.objects.filter(status="Active")
        serializer = ZoneListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AreaList(APIView):
    def get(self, request, zone):
        data = Area.objects.filter(zone=zone, status="Active")
        serializer = AreaListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SubAreaList(APIView):
    def get(self, request, area):
        data = SubArea.objects.filter(area=area, status="Active")
        serializer = SubAreaListSerializerInspector(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EntityList(APIView):
    def get(self, request, subarea):
        data = Entity.objects.filter(subarea=subarea, status="Active")
        serializer = EntityListSerializerInspector(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EntityDetails(APIView):
    def get(self, request, entity):
        data = Entity.objects.get(pk=entity)
        serializer = EntityListSerializerInspector(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SmartSearch(APIView):
    # This view returns 3 types of results.
    # Based on search types (results (search results), count (count for search results), filter (optimized data for filter))
    def get(self,request):
        kwargs = dict(request.GET)
        response = smart_search_response_creator(**kwargs)
        return response

class Locations(APIView):
    def get(self,request):
        type_of_loc = request.GET.get('type',None)
        if (type_of_loc == None):
            response = {
                'error': 'Type of location shall be specified !'
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)
            print(type_of_loc)
        if type_of_loc not in ['zone', 'area', 'subarea']:
            response = {
                'error': 'Invalid type of location !'
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        response = get_locations_for_smart_search(type_of_loc)
        # response = smart_search_response_creator(**kwargs)
        return response

class EntityUpdateView(APIView):
    def post(self,request, pk):
        data = request.data
        print(data)
        entity = Entity.objects.filter(pk=pk)
        if len(entity) == 0:
            return Response({'error' : 'Invalid Entity ID'}, status=status.HTTP_404_NOT_FOUND)
        entity = entity[0]
        fields_and_values = data
        fields_and_values_array = list(fields_and_values.keys())
        remarks = ''
        for item in fields_and_values_array:
            remarks += f"{item.capitalize().replace('_',' ')} has been modified by {request.user.full_name} from {str(entity.__dict__[item]).replace('_',' ')} to {str(data[item]).replace('_',' ')} & "
        EntityLog.objects.create(
            action_taken = 'Updated',
            action_taken_by = request.user,
            action_taken_on_id = pk,
            fields_and_values = data,
            remarks = remarks
        )
        entity.modification_pending = True
        entity.save()
        return Response('updated', status=status.HTTP_200_OK)

class EntityDetailsForInspector(APIView):
    def get_object(self, pk):
        try:
            return Entity.objects.get(pk=pk)
        except Entity.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityListSerializer(data).data
        modificationApprovalPendingFields = {}
        if (data.modification_pending):
            last_log = EntityLog.objects.filter(action_taken_by=request.user, action_taken_on_id = pk)
            if (len(last_log) != 0):
                # Now we need to check the history of update of this partical user on the entity. 
                # If the update was approved by admin, then we will sent modificationApprovalPendingFields is empty
                # Else we have to send the last update done by the user
                last_log = last_log.last()
                approved_log = EntityLog.objects.filter(related_self_log=last_log.id)
                modificationApprovalPendingFields = last_log.fields_and_values
                if (len(approved_log) != 0):
                    last_approved_log = approved_log.last()
                    if (last_approved_log.action_taken == 'UpdateApproved' or last_approved_log.action_taken == 'UpdateRejected'):
                        modificationApprovalPendingFields = {}
        # breakpoint()
        # The modification pending empty means, eventhough there is a pending modification, 
        #  it was not done by the requested user and we dont need to inform him about the same 
        if (len(modificationApprovalPendingFields) == 0):
            serializer['modification_pending'] = False
        serializer['modificationApprovalPendingFields'] = modificationApprovalPendingFields
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

class EntityInspection(APIView):

    def get(self, request):
        data = EntityInspection.objects.exclude(status="Deleted")
        serializer = EntityInspectionSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = EntityInspectionSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(EntityInspectionSerializer(data).data, status=status.HTTP_200_OK)

class EntityInspectionDetails(APIView):

    def get_object(self, pk):
        try:
            return EntityInspection.objects.get(pk=pk)
        except EntityInspection.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityInspectionSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = EntityInspectionSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(EntityInspectionSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EntityGreaseTrapInspection(APIView):

    def get(self, request):
        data = EntityGreaseTrapInspection.objects.exclude(status="Deleted")
        serializer = EntityGreaseTrapInspectionSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = EntityGreaseTrapInspectionSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.save(created_by = request.user)
        return Response(EntityGreaseTrapInspectionSerializer(data).data, status=status.HTTP_200_OK)