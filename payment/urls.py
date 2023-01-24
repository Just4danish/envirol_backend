from django.urls import path
from .views import *

urlpatterns = [
    path('get_payment_payload', GetPaymentPayload.as_view()),
    path('checkout_details', CheckoutDetails.as_view()),
    path('checkout_status', CheckoutStatus.as_view()),
]