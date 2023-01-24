from django.urls import path
from .views import *

urlpatterns = [
    path('invite_user', InviteUserView.as_view()),
    path('activate_invitation/<str:key>', ActivateInvitationView.as_view()),
    path('resend_invitation/<int:pk>', ResendInvitationView.as_view()),
    path('envirol_user', EnvirolUserView.as_view()),
    path('foodwatch_user', FoodwatchUserView.as_view()),
    path('login', LoginView.as_view()),
    path('logout', LogoutView.as_view()),
    path('profile', ProfileView.as_view()),
    path('change_password', ChangePasswordView.as_view()),
    path('send_forgot_password_otp', SendForgotPasswordOTP.as_view()),
    path('validate_forgot_password_otp', ValidateForgotPasswordOTP.as_view()),
    path('gate_operator', GateOperatorView.as_view()),
    path('inspector', InspectorView.as_view()),
    path('user', UserListView.as_view()),
    path('user/<int:pk>', UserDetails.as_view()),
]