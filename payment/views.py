from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from gtcc.models import CheckoutDetail, GTCC, PaymentDetail
from masters.models import ModeOfPayment
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from abacimodules.permissions import IsGTCCUser
from django.http import HttpResponseRedirect
from .serializers import *
import xmltodict
from django.conf import settings
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
import time
from Crypto.Util.Padding import pad, unpad
from django.utils import timezone
    
class GetPaymentPayload(APIView):
    permission_classes = [IsAuthenticated, IsGTCCUser]
    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user        = request.user
        gtcc        = user.link_id
        amount      = serializer.validated_data.get('amount')
        paid_amount = serializer.validated_data.get('paid_amount')
        try:
            gtcc_obj = GTCC.objects.get(pk=gtcc, status='Active')
        except GTCC.DoesNotExist:
            return Response("GTCC not found", status=status.HTTP_400_BAD_REQUEST)
        ts = time.time()
        timestamp = str(ts).replace(".", "")
        checkout = CheckoutDetail(
            gtcc            =   gtcc_obj,
            amount          =   amount,
            service_charge  =   serializer.validated_data.get('service_charge'),
            paid_amount     =   paid_amount,
            created_by      =   user,
            type_of_payment =   serializer.validated_data.get('type_of_payment')
        )
        checkout.save()
        client_id       = settings.CBD_CLIENT_ID
        order_id        = str(checkout.id)+timestamp
        redirect_url    = "https://fogwatch.envirol.ae/payment/checkout_status"
        data            = "<BankInformation><ClientID>"+client_id+"</ClientID><ReturnPage>"+redirect_url+"</ReturnPage><CreateToken>false</CreateToken><locale>en-us</locale><PaymentInformation><OrderID>"+str(order_id)+"</OrderID><TotalAmount>"+str(paid_amount)+"</TotalAmount><TransactionType>sale</TransactionType><OrderDescription>TEST Description</OrderDescription><Currency>AED</Currency></PaymentInformation></BankInformation>"
        xml_payload     = crypto_encrypt(data)
        checkout.payload    = data
        checkout.order_id   = order_id
        checkout.save()
        return Response(xml_payload, status=status.HTTP_200_OK)

class CheckoutDetails(generics.ListAPIView):
    serializer_class = CheckoutListSerializer
    queryset = CheckoutDetail.objects.all()

class CheckoutStatus(APIView):
    permission_classes = [AllowAny]
    @transaction.atomic
    def post(self, request):
        data = request.data.get('c', None)
        success_url = 'https://fogwatch.envirol.ae/paymentsuccess/'
        failed_url  = 'https://fogwatch.envirol.ae/paymentfail/'
        if data == None:
            response_msg = "Bank server error"
            failed_url += b64encode(response_msg.encode()).decode()
            return HttpResponseRedirect(redirect_to=failed_url)
        xml_response    = crypto_decrypt(data)
        dict_response   = xmltodict.parse(xml_response)
        response        = dict_response['Response']
        header              = response['Header']
        body                = response['Body']
        response_code       = header['ResponseCode']
        response_msg        = header['ResponseMsg']
        payment_information = body['PaymentInformation']
        cbd_reference_no    = payment_information['CBDReferenceNo']
        cc_reference_no     = payment_information['CCReferenceNo']
        order_id            = payment_information['OrderID']
        payment_date        = payment_information['PaymentDate']
        payment_time        = payment_information['PaymentTime']
        try:
            checkout = CheckoutDetail.objects.get(order_id=order_id)
        except CheckoutDetail.DoesNotExist:
            response_msg = "Payment request rejected"
            failed_url += b64encode(response_msg.encode()).decode()
            return HttpResponseRedirect(redirect_to=failed_url)
        checkout.response = xml_response
        if response_code == "00":
            gtcc                = checkout.gtcc
            amount              = checkout.amount
            created_by          = checkout.created_by
            credit_available    = checkout.gtcc.credit_available
            previous_balance    = credit_available
            new_balance         = credit_available + amount
            mode_of_payment     = ModeOfPayment.objects.get(pk=1)
            try:
                PaymentDetail.objects.create(
                    gtcc                = gtcc,
                    mode_of_payment     = mode_of_payment,
                    checkout            = checkout,
                    amount              = amount,
                    previous_balance    = previous_balance,
                    new_balance         = new_balance,
                    txn_no              = order_id,
                    reference_no        = cbd_reference_no,
                    payment_date        = timezone.now(),
                    payment_type        = 'Credit',
                    created_by          = created_by
                )
            except:
                pass
            checkout.status = 'Success'
            checkout.save()
            gtcc.credit_available = new_balance
            gtcc.save()
            response_msg = f'AED {amount} has been credited to your account'
            success_url += b64encode(response_msg.encode()).decode()
            return HttpResponseRedirect(redirect_to=success_url)
        else:
            checkout.status = 'Failed'
            checkout.save()
            failed_url += b64encode(response_msg.encode()).decode()
            return HttpResponseRedirect(redirect_to=failed_url)

def crypto_encrypt(data):
    try:
        encryption_key  = settings.CBD_ENCRYPTION_KEY
        encryption_key  = encryption_key.encode('utf-8')
        cipher          = AES.new(encryption_key, AES.MODE_CBC, encryption_key)
        ct_bytes        = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        xml_payload     = b64encode(ct_bytes).decode('utf-8')
        return xml_payload
    except:
        print("Incorrect encryption")

def crypto_decrypt(data):
    try:
        encryption_key  = settings.CBD_ENCRYPTION_KEY
        encryption_key  = encryption_key.encode('utf-8')
        ct = b64decode(data)
        cipher = AES.new(encryption_key, AES.MODE_CBC, encryption_key)
        xml_response = unpad(cipher.decrypt(ct), AES.block_size)
        return xml_response.decode('utf-8')
    except:
        print("Incorrect decryption")