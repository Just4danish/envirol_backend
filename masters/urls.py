from django.urls import path
from .views import *

urlpatterns = [
    path('main_category', MainCategoryList.as_view()),
    path('main_category/<int:pk>', MainCategoryDetails.as_view()),
    path('sub_category', SubCategoryList.as_view()),
    path('sub_category/<int:pk>', SubCategoryDetails.as_view()),
    path('mode_of_payment', ModeOfPaymentList.as_view()),
    path('mode_of_payment/<int:pk>', ModeOfPaymentDetails.as_view()),
    path('grease_trap', GreaseTrapList.as_view()),
    path('grease_trap/<int:pk>', GreaseTrapDetails.as_view()),
    path('fixture', FixtureList.as_view()),
    path('fixture/<int:pk>', FixtureDetails.as_view()),
    path('zone', ZoneList.as_view()),
    path('zone/<int:pk>', ZoneDetails.as_view()),
    path('area', AreaList.as_view()),
    path('area/<int:pk>', AreaDetails.as_view()),
    path('subarea', SubAreaList.as_view()),
    path('subarea/<int:pk>', SubAreaDetails.as_view()),
    path('designation', DesignationList.as_view()),
    path('designation/<int:pk>', DesignationDetails.as_view()),
    path('gate', GateList.as_view()),
    path('gate/<int:pk>', GateDetails.as_view()),
    path('rfid_card', RFIDCardList.as_view()),
    path('rfid_card/<int:pk>', RFIDCardDetails.as_view()),
    path('unused_rfid_cards', UnusedRFIDCards.as_view()),
    path('notification',NotificationList.as_view()),
    path('notification/<int:pk>',NotificationDetails.as_view()),
    path('get_active_notification',GetActiveNotification.as_view()),
]