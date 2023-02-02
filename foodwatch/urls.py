from django.urls import path
from .views import *

urlpatterns = [
    path('get_token', GetToken.as_view()),
    path('get_grease_trap_info', EntityGreaseTrapList.as_view()),
    path('create_service_request', CreateServiceRequest.as_view()),
    path('sync_foodwatch_enitity', sync_foodwatch_enitity),
    path('entity', EntityList.as_view()),
    path('entity/<int:pk>', EntityDetails.as_view()),
    path('convert_entity/<int:pk>', ConvertEntity.as_view()),
    path('delete_entity/<int:pk>', DeleteEntity.as_view()),
]