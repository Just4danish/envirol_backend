from django.utils.crypto import get_random_string
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from django.conf import settings
from random import randint
from abacimodules.email_engine import *
from django.core.validators import RegexValidator,validate_email
from django.utils.translation import gettext as _
from django.core.exceptions import BadRequest
import threading
from django.template.loader import render_to_string 
from django.core.mail import EmailMessage
import time

class MyUserManager(BaseUserManager):
    def create_user(self, username, first_name, password):
        # if not email:
        #     raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            first_name=first_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, first_name, password=None):
        try:
            validate_email(username)
        except:
            raise ValueError('Super users must have an email address')
        user = self.create_user(
            username,
            password=password,
            first_name=first_name,
        )
        user.email = username
        user.user_status = 'Activated'
        user.user_class = 'Envirol'
        user.user_type = 'Admin'
        user.save(using=self._db)
        return user


def content_file_name(instance, filename):
    path = 'avatars/' + str(instance.id) + '/' + f'{str(instance.id)}_{time.time()}.png'
    return path

no_space_validator = RegexValidator(
    r' ',
    _('No spaces allowed'),
    inverse_match=True,
    code='invalid_tag',
)

class Account(AbstractBaseUser):
    username = models.CharField(verbose_name='username', max_length=255, unique=True, validators=[no_space_validator])
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    first_name = models.CharField(max_length=50, default = "")
    last_name = models.CharField(max_length=50, default = "", null=True)
    full_name = models.CharField(max_length=50, null=True)
    emp_id = models.CharField(max_length=50, null=True)
    link_id = models.IntegerField(null=True)
    link_class = models.CharField(max_length=50, null=True)
    designation = models.ForeignKey("masters.Designation", related_name='user_designation', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_vehicle = models.ForeignKey("gtcc.VehicleDetail", related_name='assigned_vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    license_no = models.CharField(max_length=50, null=True)
    extension_number = models.CharField(max_length=100, null=True)
    contact_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=100, null=True)
    emirate = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.ImageField(upload_to=content_file_name, null=True, blank=True)
    retrieve_password_otp = models.IntegerField(blank=True, null=True)
    retrieve_password_otp_expired = models.BooleanField(default=True)
    inviting_key = models.CharField(max_length=100, blank=True, null=True)
    registration_key = models.CharField(max_length=100, blank=True, null=True)
    api_key = models.CharField(max_length=100, blank=True, null=True)
    inviter = models.ForeignKey('self', related_name='inviter_user', on_delete=models.SET_NULL, null=True)
    invited_date = models.DateTimeField(verbose_name='created', auto_now_add=True)
    invite_expiry_date = models.DateTimeField(verbose_name='created', null=True)
    is_staff = models.BooleanField(default=False)
    user_status_choice = [('Invited', 'Invited'), ('Activated', 'Activated'), ('Deactivated', 'Deactivated'), ('Deleted', 'Deleted')]
    user_status = models.CharField(max_length=100, choices=user_status_choice, default='Invited')
    user_classes = [('Envirol', 'Envirol'), ('GTCC', 'GTCC'), ('Entity', 'Entity'), ('Foodwatch', 'Foodwatch')]
    user_class   = models.CharField(max_length=10, choices=user_classes)
    user_types  = [('Admin', 'Admin'), ('User', 'User'), ('Driver', 'Driver'), ('Inspector', 'Inspector'), ('Operator', 'Operator')]
    user_type   = models.CharField(max_length=10, choices=user_types)
    modified_by = models.ForeignKey('self', related_name='account_modified_by', on_delete=models.SET_NULL, null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True)

    objects = MyUserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name']

    def save(self, *args, **kwargs):
        self.username = self.username.lower()
        self.email = self.email.lower()
        self.first_name = self.first_name.capitalize()
        if (self.last_name != None):
            self.last_name = self.last_name.capitalize()
            self.full_name = f"{self.first_name} {self.last_name}"
        else:
            self.full_name = self.first_name
        if self.pk == None:
            self.api_key = get_random_string(32).lower()
        super().save(*args, **kwargs)
        return self

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def forgot_password(self):
        if not self.email:
            raise BadRequest("Forgot user function not allowed for this user.")
        self.retrieve_password_otp = randint(100000, 999999)
        self.retrieve_password_otp_expired = False
        self.save()
        subject = "Reset Your Password"
        template_name = 'users/forgot_password.html'
        context = {
            "otp": self.retrieve_password_otp,
            "name" : self.first_name
        }
        receivers = [self.email]
        html_message = render_to_string(template_name, context)
        temp_emailsending = SendEmail(subject, html_message, receivers).start()


    def send_invitation(self):
        if not self.email:
            raise BadRequest("No email associated with the user.")
        email = self.email
        inviter = self.inviter
        url = settings.FRONTEND_HOST + 'register/' + self.inviting_key
        template_name = 'users/invite_email.html'

        if (isinstance(self.first_name, type(None))):
            invitee_name = "Invitee"
        else:
            invitee_name = self.first_name
            if (isinstance(self.last_name, type(None))):
                pass
            else:
                invitee_name += " " + self.last_name

        if (isinstance(self.inviter.first_name, type(None))):
            inviter_name = "Inviter"
        else:
            inviter_name = self.inviter.first_name
            if (isinstance(self.inviter.last_name, type(None))):
                pass
            else:
                inviter_name += " " + self.inviter.last_name

        subject = "Invitation to Join Fogwatch"
        context = {
            "invitee": invitee_name,
            "inviter" : inviter_name,
            "link" : url
        }
        receivers = [self.email]
        html_message = render_to_string(template_name, context)
        temp_emailsending = SendEmail(subject, html_message, receivers).start()

    def send_api_key(self):
        template_name = 'users/api_key.html'
        subject = "Account Activated"
        context = {
            "user": self.full_name,
            "api_key" : self.api_key
        }
        receivers = [self.email]
        html_message = render_to_string(template_name, context)
        SendEmail(subject, html_message, receivers).start()

class LoginDetail(models.Model):
    user = models.ForeignKey(Account, related_name='logged_user', on_delete=models.CASCADE, null=True)
    ip_address = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    choices = [
        ('Success', 'Success'), 
        ('Failed', 'Failed'),
    ]
    status = models.CharField(max_length=100, choices=choices)
    log_type_choices = [
        ('Login', 'Login'), 
        ('Logout', 'Logout'),
    ]
    log_type = models.CharField(max_length=100, choices=log_type_choices, default='Login')
    reason = models.CharField(max_length=200, null=True)


class SendEmail(threading.Thread):
    def __init__(self, subject, html_message, receivers, attachment=None):
        self.subject        = subject
        self.html_message   = html_message
        self.sender         = settings.SENDER_EMAIL
        self.receivers      = receivers
        self.attachment     = attachment
        threading.Thread.__init__(self)
    def run(self):
        message = EmailMessage(self.subject, self.html_message,self.sender,self.receivers)
        message.content_subtype = 'html'
        if self.attachment:
            message.attach_file(self.attachment)
        a = message.send()
        
