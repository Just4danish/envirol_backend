from rest_framework import authentication
import jwt
from django.conf import settings
import datetime
from django.utils import timezone

class TokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
        auth_data = authentication.get_authorization_header(request)
        if not auth_data:
            return response
        prefix, token = auth_data.decode('utf-8').split(' ')
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms="HS256")
            message = {
                'username': payload['username'], 
                'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=settings.EXPIRY_IN_MINUTES)
                }
            auth_token = jwt.encode(
                message, settings.JWT_SECRET_KEY, algorithm="HS256")
            response.set_cookie(key='token', value=auth_token, httponly=False)
            return response
        except:
            return response


