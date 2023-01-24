from django.http import Http404
from .models import *
from .serializers import *
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

class MainCategoryList(APIView):

    def get(self, request):
        data = MainCategory.objects.exclude(status="Deleted")
        serializer = MainCategoryListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = MainCategoryPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(MainCategoryListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MainCategoryDetails(APIView):

    def get_object(self, pk):
        try:
            return MainCategory.objects.get(pk=pk)
        except MainCategory.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = MainCategoryListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = MainCategoryPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(MainCategoryListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubCategoryList(APIView):

    def get(self, request):
        data = SubCategory.objects.exclude(status="Deleted")
        serializer = SubCategoryListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SubCategoryPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(SubCategoryListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubCategoryDetails(APIView):

    def get_object(self, pk):
        try:
            return SubCategory.objects.get(pk=pk)
        except SubCategory.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = SubCategoryListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = SubCategoryPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(SubCategoryListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ModeOfPaymentList(APIView):

    def get(self, request):
        data = ModeOfPayment.objects.exclude(status="Deleted")
        serializer = ModeOfPaymentListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ModeOfPaymentPostSerializer(data=request.data)
        if serializer.is_valid():
            try:
                max_id = ModeOfPayment.objects.latest('id').id + 1
            except ModeOfPayment.DoesNotExist:
                max_id = 1
            data = serializer.save(mop_id = 1000+max_id, created_by = request.user)
            return Response(ModeOfPaymentListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ModeOfPaymentDetails(APIView):

    def get_object(self, pk):
        try:
            return ModeOfPayment.objects.get(pk=pk)
        except ModeOfPayment.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = ModeOfPaymentListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = ModeOfPaymentPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(ModeOfPaymentListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GreaseTrapList(APIView):

    def get(self, request):
        limited = request.data.get('limited', False)
        data = GreaseTrap.objects.exclude(status="Deleted").order_by('description')
        if limited:
            serializer = GreaseTrapLimitedDetailsListSerializer(data, many=True)
        else:
            serializer = GreaseTrapListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = GreaseTrapPostSerializer(data=request.data)
        if serializer.is_valid():
            try:
                max_id = GreaseTrap.objects.latest('id').id + 1
            except GreaseTrap.DoesNotExist:
                max_id = 1
            data = serializer.save(grease_trap_id = 1000+max_id, created_by = request.user)
            return Response(GreaseTrapListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GreaseTrapDetails(APIView):

    def get_object(self, pk):
        try:
            return GreaseTrap.objects.get(pk=pk)
        except GreaseTrap.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = GreaseTrapListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = GreaseTrapPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(GreaseTrapListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FixtureList(APIView):

    def get(self, request):
        data = Fixture.objects.exclude(status="Deleted")
        serializer = FixtureListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = FixturePostSerializer(data=request.data)
        if serializer.is_valid():
            try:
                max_id = Fixture.objects.latest('id').id + 1
            except Fixture.DoesNotExist:
                max_id = 1
            data = serializer.save(fixture_id = 1000+max_id, created_by = request.user)
            return Response(FixtureListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FixtureDetails(APIView):

    def get_object(self, pk):
        try:
            return Fixture.objects.get(pk=pk)
        except Fixture.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = FixtureListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = FixturePostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(FixtureListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ZoneList(APIView):

    def get(self, request):
        data = Zone.objects.exclude(status="Deleted")
        serializer = ZoneListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ZonePostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(ZoneListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ZoneDetails(APIView):

    def get_object(self, pk):
        try:
            return Zone.objects.get(pk=pk)
        except Zone.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = ZoneListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = ZonePostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(ZoneListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AreaList(APIView):

    def get(self, request):
        data = Area.objects.exclude(status="Deleted")
        serializer = AreaListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = AreaPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(AreaListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AreaDetails(APIView):

    def get_object(self, pk):
        try:
            return Area.objects.get(pk=pk)
        except Area.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = AreaListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = AreaPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(AreaListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubAreaList(APIView):

    def get(self, request):
        data = SubArea.objects.exclude(status="Deleted")
        serializer = SubAreaListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SubAreaPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(SubAreaListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubAreaDetails(APIView):

    def get_object(self, pk):
        try:
            return SubArea.objects.get(pk=pk)
        except SubArea.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = SubAreaListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = SubAreaPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(SubAreaListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DesignationList(APIView):

    def get(self, request):
        data = Designation.objects.exclude(status="Deleted")
        serializer = DesignationListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = DesignationPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(DesignationListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DesignationDetails(APIView):

    def get_object(self, pk):
        try:
            return Designation.objects.get(pk=pk)
        except Designation.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = DesignationListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = DesignationPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(DesignationListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GateList(APIView):

    def get(self, request):
        data = Gate.objects.exclude(status="Deleted")
        serializer = GateListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = GatePostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(GateListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GateDetails(APIView):

    def get_object(self, pk):
        try:
            return Gate.objects.get(pk=pk)
        except Gate.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = GateListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = GatePostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(GateListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RFIDCardList(APIView):

    def get(self, request):
        data = RFIDCard.objects.exclude(status="Deleted")
        serializer = RFIDCardListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = RFIDCardPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save(created_by = request.user)
            return Response(RFIDCardListSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RFIDCardDetails(APIView):

    def get_object(self, pk):
        try:
            return RFIDCard.objects.get(pk=pk)
        except RFIDCard.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = RFIDCardListSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        data = self.get_object(pk)
        serializer = RFIDCardPostSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by = request.user)
            return Response(RFIDCardListSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnusedRFIDCards(APIView):

    def get(self, request):
        data = RFIDCard.objects.filter(vehicle__isnull = True, status='Active')
        serializer = RFIDCardLimitedListSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationList(APIView):

    def get(self, request):
        data = Notification.objects.exclude(status="Deleted")
        serializer = NotificationSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            start_time      = serializer.validated_data.get('start_time')
            end_time        = serializer.validated_data.get('end_time')
            current_time    = timezone.now()
            if start_time < current_time:
                return Response({'error' : 'Past date not allowed'}, status=status.HTTP_400_BAD_REQUEST)
            if start_time >= end_time:
                return Response({'error' : 'Start time should be less than end time'}, status=status.HTTP_400_BAD_REQUEST)
            last_notitication = Notification.objects.exclude(status='Expired').last()
            if not isinstance(last_notitication, type(None)):
                if start_time < last_notitication.end_time:
                    return Response({'error' : 'Notification start date should be greater than last notitication end date'}, status=status.HTTP_400_BAD_REQUEST)
            data = serializer.save(created_by = request.user)
            return Response(NotificationSerializer(data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationDetails(APIView):

    def get_object(self, pk):
        try:
            return Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        data = self.get_object(pk)
        serializer = NotificationSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        data = self.get_object(pk)
        serializer = NotificationSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            start_time      = serializer.validated_data.get('start_time')
            end_time        = serializer.validated_data.get('end_time')
            current_time    = timezone.now()
            if start_time < current_time:
                return Response({'error' : 'Past date not allowed'}, status=status.HTTP_400_BAD_REQUEST)
            if start_time >= end_time:
                return Response({'error' : 'Start time should be less than end time'}, status=status.HTTP_400_BAD_REQUEST)
            previous_notitication = Notification.objects.exclude(status='Expired').filter(id__lt=pk).last()
            if not isinstance(previous_notitication, type(None)):
                if start_time < previous_notitication.end_time:
                    return Response({'error' : 'Notification start date should be greater than last notitication end date'}, status=status.HTTP_400_BAD_REQUEST)
            post_notitication = Notification.objects.exclude(status='Expired').filter(id__gt=pk).first()
            if not isinstance(post_notitication, type(None)):
                if end_time > post_notitication.start_time:
                    return Response({'error' : 'Notification end date should be less than post notitication start date'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(modified_by = request.user)
            return Response(NotificationSerializer(data).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetActiveNotification(APIView):

    def get(self, request):
        try:
            notification = Notification.objects.get(status='Active')
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            raise Http404

        
