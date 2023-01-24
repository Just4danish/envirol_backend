from django.urls import path
from .views import *

urlpatterns = [
    path('entity', EntityList.as_view()),
    path('entity/<int:pk>', EntityDetails.as_view()),
    path('change_entity_image/<int:pk>', ChangeEntityImage.as_view()),
    path('fixture', EntityFixtureList.as_view()),
    path('fixture/<int:pk>', EntityFixtureDetails.as_view()),
    path('grease_trap', EntityGreaseTrapList.as_view()),
    path('grease_trap/<int:pk>', EntityGreaseTrapDetails.as_view()),
    path('entity_gtcc', EntityGTCCList.as_view()),
    path('entity_gtcc/<int:pk>', EntityGTCCDetails.as_view()),
    path('entity_qrcode_scan', EntityQRCodeScan.as_view()),
    path('service_request', ServiceRequestList.as_view()),
    path('entity_service_request_list/<int:pk>', EntityServiceRequestListView.as_view()),
    path('manage_entity_grease_trap', ManageEntityGreaseTrap.as_view()),
    path('entity_with_grease_traps', EntityWithGreaseTraps.as_view()),
    path('convert_coupon_to_sr', ConvertCouponToSR.as_view()),
    path('service_request_log/<int:service_request_id>', ServiceRequestLogList.as_view()),
]