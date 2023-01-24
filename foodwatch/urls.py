from django.urls import path
from .views import *

urlpatterns = [
    path('get_token', GetToken.as_view()),
    path('get_grease_trap_info', EntityGreaseTrapList.as_view()),
    path('create_service_request', CreateServiceRequest.as_view()),
]