from django.db import models
from users.models import Account
from django.core.validators import MaxValueValidator, MinValueValidator
import time

choices = [('Active', 'Active'), ('Approval Pending' , 'Approval Pending'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted'), ('Rejected', 'Rejected')]

def content_file_name(instance, filename):
    path = 'gtcc_image/' + str(instance.id) + '/' + f'{str(instance.id)}_{time.time()}.png'
    return path

class GTCC(models.Model):
    establishment_name = models.CharField(max_length=255)
    trade_license_no = models.CharField(max_length=100, null=True)
    trade_license_name = models.CharField(max_length=100, null=True)
    env_sap_id = models.CharField(max_length=100,null=True)
    image = models.ImageField(upload_to=content_file_name, null=True)
    credit_available = models.DecimalField(max_digits=12, decimal_places=1, default=0)
    active_contact_person = models.ForeignKey(Account, related_name='active_contact_person', on_delete=models.CASCADE, null=True)
    foodwatch_id = models.IntegerField(null=True)
    foodwatch_business_id = models.IntegerField(null=True)
    address = models.CharField(max_length=255, null=True)
    phone_no = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=100, null=True)
    location_remark = models.CharField(max_length=255, null=True)
    po_box = models.CharField(max_length=50, null=True)
    website_url = models.CharField(max_length=255, null=True)
    office_email = models.EmailField(null=True)
    created_by = models.ForeignKey(Account, related_name='gtcc_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='gtcc_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=choices, default='Active')

class PaymentDetail(models.Model):
    gtcc = models.ForeignKey(GTCC, related_name='payment_detail_gtcc', on_delete=models.CASCADE)
    mode_of_payment = models.ForeignKey('masters.ModeOfPayment', related_name='payment_detail_mode_of_payment', on_delete=models.CASCADE)
    checkout = models.ForeignKey('CheckoutDetail', related_name='payment_detail_checkout', on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(1)])
    previous_balance = models.DecimalField(max_digits=12, decimal_places=2)
    new_balance = models.DecimalField(max_digits=12, decimal_places=2)
    txn_no = models.CharField(max_length=100)
    reference_no = models.CharField(max_length=100)
    payment_date = models.DateField()
    payment_types = [('Credit', 'Credit'), ('Debit', 'Debit')]
    payment_type = models.CharField(max_length=10, choices=payment_types)
    created_by = models.ForeignKey(Account, related_name='payment_detail_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='payment_detail_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status_choices = [('Approved', 'Approved'), ('Pending Approval', 'Pending Approval'), ('Canceled', 'Canceled')]
    status = models.CharField(max_length=20, choices=status_choices, default='Approved')

class CheckoutDetail(models.Model):
    gtcc = models.ForeignKey(GTCC, related_name='checkout_gtcc', on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=1, validators=[MinValueValidator(1), MaxValueValidator(100000)])
    service_charge = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payload = models.TextField(null=True)
    response = models.TextField(null=True)
    created_by = models.ForeignKey(Account, related_name='checkout_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    type_of_payment_choices = [('Card', 'Card'), ('Bank', 'Bank')]
    type_of_payment = models.CharField(max_length=10, choices=type_of_payment_choices)
    status_choices = [('Initiated', 'Initiated'), ('Success', 'Success'), ('Failed', 'Failed')]
    status = models.CharField(max_length=20, choices=status_choices, default='Initiated')

class VehicleDetail(models.Model):
    gtcc = models.ForeignKey(GTCC, related_name='vehicle_detail_gtcc', on_delete=models.CASCADE)
    driver = models.ForeignKey(Account, related_name='vehicle_driver', on_delete=models.CASCADE, null=True, blank=True)
    vehicle_no = models.CharField(max_length=100, unique=True)
    chassis_no = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=100)
    vehicle_tank_capacity = models.DecimalField(max_digits=12, decimal_places=2)
    random_key = models.CharField(max_length=100)
    created_by = models.ForeignKey(Account, related_name='vehicle_detail_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='vehicle_detail_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=choices, default='Active')
    # entry_choices = [('Entered','Entered'),('Exited','Exited')]
    # envirol_entry_status = models.CharField(max_length=10, choices=entry_choices, default='Exited')

class Booklet(models.Model):
    booklet_no = models.CharField(max_length=100, unique=True)
    coupon_start_no = models.PositiveIntegerField()
    created_by = models.ForeignKey(Account, related_name='booklet_creator', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='booklet_modifier', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(null=True)
    status_choices = [('Active', 'Active'), ('Issued', 'Issued'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')]
    status = models.CharField(max_length=20, choices=status_choices, default='Active')

class CouponBooklet(models.Model):
    booklet = models.OneToOneField(Booklet, on_delete=models.CASCADE)
    coupon_end_no = models.PositiveIntegerField()
    total_coupons = models.PositiveIntegerField()
    used_coupons = models.PositiveIntegerField(default=0)
    gtcc = models.ForeignKey(GTCC, related_name='booklet_assigned_gtcc', on_delete=models.CASCADE)
    vehicle = models.ForeignKey(VehicleDetail, related_name='booklet_assigned_vehicle', on_delete=models.CASCADE, null=True)
    collected_by = models.CharField(max_length=100, null=True)
    collected_on = models.DateField(null=True)
    created_by = models.ForeignKey(Account, related_name='booklet_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='booklet_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(null=True)
    booklet_choices = [('Issued', 'Issued'), ('In Use', 'In Use'), ('Used', 'Used')]
    status = models.CharField(max_length=20, choices=booklet_choices, default='Issued')

def content_file_name(instance, filename):
    path = f"coupons/{instance.booklet.id}/{instance.coupon_no}_{filename[-5:]}"
    return path


class Coupon(models.Model):
    booklet = models.ForeignKey(CouponBooklet, related_name='coupon_booklet', on_delete=models.CASCADE)
    coupon_no = models.PositiveIntegerField()
    returned_on = models.DateTimeField(null=True)
    returned_by = models.ForeignKey(Account, related_name='coupon_returned_by', on_delete=models.CASCADE, null=True)
    collected_by = models.ForeignKey(Account, related_name='coupon_collected_by', on_delete=models.CASCADE, null=True)
    collected_remark = models.TextField(null=True)
    collection_violation = models.BooleanField(default=False)
    total_gallons = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    converted_on = models.DateTimeField(null=True)
    converted_by = models.ForeignKey(Account, related_name='coupon_converted_by', on_delete=models.CASCADE, null=True)
    service_request = models.ForeignKey('entity.ServiceRequest', related_name='coupon_service_request', on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to=content_file_name, null=True)
    vehicle = models.ForeignKey(VehicleDetail, related_name='coupon_vehicledetail', on_delete=models.CASCADE, null=True)
    dumping_vehicledetails = models.ForeignKey('VehicleEntryDetails', related_name='coupon_dumped_vehicledetails', on_delete=models.CASCADE, null=True)
    coupon_choices = [('Issued', 'Issued'), ('Scanned', 'Scanned'), ('Used', 'Used'), ('Converted', 'Converted'), ('Lost', 'Lost')]
    status = models.CharField(max_length=20, choices=coupon_choices, default='Issued')

class AccessControlLog(models.Model):
    vehicle = models.ForeignKey(VehicleDetail, related_name='accesscontrollog_vehicledetail', on_delete=models.CASCADE)
    driver = models.ForeignKey(Account, related_name='accesscontrollog_driver', on_delete=models.CASCADE, null=True)
    operator = models.ForeignKey(Account, related_name='accesscontrollog_operator', on_delete=models.CASCADE, null=True)
    rfid_card = models.ForeignKey('masters.RFIDCard', related_name='accesscontrollog_rfid', on_delete=models.CASCADE, null=True)
    accessed_gate = models.ForeignKey('masters.Gate', related_name='gate_vehicledetail', on_delete=models.CASCADE)
    status_choice = [("Entered","Entered"),("Approved","Approved"),("Rejected","Rejected"),("Discharged","Discharged"),("Exited","Exited")]
    status = models.CharField(max_length=20, choices=status_choice,null=True)
    accessed_time = models.DateTimeField(auto_now_add=True)
    direction_choice = [("Entry","Entry"),("Exit","Exit")]
    accessed_direction = models.CharField(max_length=10, choices=direction_choice,null=True)

class VehicleEntryDetails(models.Model):
    txn_id = models.CharField(max_length=100, null=True)
    vehicle = models.ForeignKey(VehicleDetail, related_name='vehicleentrydetails_vehicle', on_delete=models.CASCADE)
    driver = models.ForeignKey(Account, related_name='vehicleentrydetails_driver', on_delete=models.CASCADE)
    gtcc = models.ForeignKey(GTCC, related_name='vehicleentrydetails_gtcc', on_delete=models.CASCADE)
    entry_time = models.DateTimeField(null=True)
    exit_time = models.DateTimeField(null=True)
    total_gallon_collected = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_dumping_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_gallon_dumped = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    operator = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    operator_acceptance_choice = [("Pending","Pending"),("Accepted","Accepted"),("Rejected","Rejected")]
    operator_acceptance = models.CharField(max_length=10, choices=operator_acceptance_choice, default='Pending')
    remarks = models.TextField(null=True)
    job_log = models.JSONField(null=True)
    delivery_order_file = models.FileField(null=True)
    current_status_choice = [("Entered","Entered"),("Exited","Exited")]
    current_status = models.CharField(max_length=10, choices=current_status_choice)

    class Meta:
        ordering = ('entry_time',)

    def save(self, *args, **kwargs):
        if self.pk is None:
            try:
                max_id = VehicleEntryDetails.objects.latest('id').id + 1
            except VehicleEntryDetails.DoesNotExist:
                max_id = 1
            self.txn_id = "DT" + str("{:06d}".format(max_id))
        super().save(*args, **kwargs)
        return self
    
class DeliveryOrderReport(models.Model):
    vehicle_entry_details = models.ForeignKey(VehicleEntryDetails, related_name='do_vehicle_entry_details', on_delete=models.CASCADE)
    pdf_content = models.JSONField()
    created_by = models.ForeignKey(Account, related_name='do_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='do_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(null=True)

class EditCouponLog(models.Model):
    coupon = models.ForeignKey(Coupon, related_name='edited_coupon', on_delete=models.CASCADE)
    change = models.TextField()
    edited_by = models.ForeignKey(Account, related_name='coupon_edited_by', on_delete=models.CASCADE)
    edited_date = models.DateTimeField(auto_now_add=True)
