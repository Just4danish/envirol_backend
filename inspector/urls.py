from django.urls import path
from .views import *

urlpatterns = [
    path('zone', ZoneList.as_view()),
    path('area/<int:zone>', AreaList.as_view()),
    path('sub_area/<int:area>', SubAreaList.as_view()),
    path('entity/<int:subarea>', EntityList.as_view()),
    path('entity_details/<int:entity>', EntityDetails.as_view()),
    path('entity_update/<int:pk>', EntityUpdateView.as_view()),
    path('entity_for_inspector/<int:pk>', EntityDetailsForInspector.as_view()),
    path('search/', SmartSearch.as_view()),
    path('locations/', Locations.as_view()),
    # path('filter_count/', FilterCount.as_view()),
]