from django.db import models
from gtcc.models import VehicleDetail
from users.models import Account


choices = [('Active', 'Active'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')]

class Unitprice(models.Model):
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=1.5)
    currency = models.CharField(max_length=25, default='AED')

class MainCategory(models.Model):
    main_category = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(Account, related_name='main_category_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='main_category_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class SubCategory(models.Model):
    main_category = models.ForeignKey(MainCategory, related_name="sub_main_category", on_delete=models.CASCADE)
    sub_category = models.CharField(max_length=100)
    created_by = models.ForeignKey(Account, related_name='sub_category_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='sub_category_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class ModeOfPayment(models.Model):
    mop_id = models.CharField(max_length=100, unique=True)
    mode_of_payment = models.CharField(max_length=100, unique=True)
    is_editable = models.BooleanField(default=True)
    created_by = models.ForeignKey(Account, related_name='mode_of_payment_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='mode_of_payment_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class GreaseTrap(models.Model):
    grease_trap_id = models.CharField(max_length=100, unique=True)
    foodwatch_id = models.CharField(max_length=100, unique=True, null=True)
    part_no = models.CharField(max_length=100)
    description = models.CharField(max_length=250, null=True)
    capacity = models.DecimalField(max_digits=6, decimal_places=2)
    material = models.CharField(max_length=100)
    shape = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    width = models.DecimalField(max_digits=6, decimal_places=2)
    length = models.DecimalField(max_digits=6, decimal_places=2)
    height = models.DecimalField(max_digits=6, decimal_places=2)
    height_to_outlet_pipe = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='grease_traps', null=True, blank=True)
    catalog = models.FileField(upload_to='grease_traps_catalogs', null=True, blank=True)
    remarks = models.CharField(max_length=100)
    created_by = models.ForeignKey(Account, related_name='grease_trap_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='grease_trap_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class Fixture(models.Model):
    fixture_id = models.CharField(max_length=100, unique=True)
    fixture = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='fixtures', null=True, blank=True)
    created_by = models.ForeignKey(Account, related_name='fixture_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='fixture_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class Zone(models.Model):
    zone_no = models.CharField(max_length=100, unique=True)
    zone_name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(Account, related_name='zone_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='zone_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class Area(models.Model):
    zone = models.ForeignKey(Zone, related_name="area_zone", on_delete=models.CASCADE)
    area_code = models.CharField(max_length=100, unique=True)
    area = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(Account, related_name='area_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='area_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class SubArea(models.Model):
    zone = models.ForeignKey(Zone, related_name="sub_area_zone", on_delete=models.CASCADE)
    area = models.ForeignKey(Area, related_name="sub_area_area", on_delete=models.CASCADE)
    sub_area = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(Account, related_name='sub_area_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='sub_area_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class Designation(models.Model):
    designation = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(Account, related_name='designation_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='designation_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class Gate(models.Model):
    gate_name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(Account, related_name='gate_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='gate_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class RFIDCard(models.Model):
    tag_id = models.CharField(max_length=250, unique=True)
    friendly_name = models.CharField(max_length=250, null=True)
    vehicle = models.OneToOneField(VehicleDetail, related_name='rfid_vehicle', on_delete=models.CASCADE, null=True)
    created_by = models.ForeignKey(Account, related_name='rfid_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='rfid_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

class Notification(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.ImageField(upload_to='notification_images')
    created_by = models.ForeignKey(Account, related_name='notification_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='notification_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    notification_choices = [('Active', 'Active'), ('Expired', 'Expired'), ('Queued', 'Queued')]
    status = models.CharField(max_length=10, choices=notification_choices, default='Queued')

