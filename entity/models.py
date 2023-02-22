from django.db import models
import datetime
from masters.models import MainCategory, SubCategory, Zone, Area, SubArea, Fixture, GreaseTrap
from gtcc.models import GTCC, VehicleDetail, VehicleEntryDetails
from django.core.validators import MaxValueValidator, MinValueValidator
from users.models import Account
import time

choices = [('Active', 'Active'), ('Disabled', 'Disabled'), ('Deleted', 'Deleted')]
entity_choices = [('Active' , 'Active') , ('Expired' , 'Expired')]

def content_file_name(instance, filename):
    path = 'entity_image/' + str(instance.id) + '/' + f'{str(instance.id)}_{time.time()}.png'
    return path

class Entity(models.Model):
    establishment_name = models.CharField(max_length=255)
    trade_license_no = models.CharField(max_length=100, null=True, blank=True)
    trade_license_name = models.CharField(max_length=100, null=True, blank=True)
    env_sap_id = models.CharField(max_length=100,null=True)
    image = models.ImageField(upload_to=content_file_name, null=True)
    active_contact_person = models.ForeignKey(Account, related_name='entity_active_contact_person', on_delete=models.PROTECT, null=True)
    active_gtcc_detail = models.ForeignKey('EntityGTCC', related_name='entity_active_gtcc', on_delete=models.PROTECT, null=True)
    foodwatch_id = models.IntegerField(null=True, blank=True)
    foodwatch_business_id = models.IntegerField(null=True, blank=True)
    job_card_no = models.CharField(max_length=100, null=True)
    category = models.ForeignKey(MainCategory, related_name='entity_category', on_delete=models.PROTECT)
    sub_category = models.ForeignKey(SubCategory, related_name='entity_subcategory', on_delete=models.PROTECT)
    zone = models.ForeignKey(Zone, related_name='entity_zone', on_delete=models.PROTECT)
    area = models.ForeignKey(Area, related_name='entity_area', on_delete=models.PROTECT)
    subarea = models.ForeignKey(SubArea, related_name='entity_subarea', on_delete=models.PROTECT)
    address = models.CharField(max_length=255, null=True)
    phone_no = models.CharField(max_length=50, null=True, blank=True)
    office_email = models.EmailField(null=True)
    entity_location = models.CharField(max_length=255, null=True, blank=True)
    location_remark = models.CharField(max_length=255, null=True, blank=True)
    po_box = models.CharField(max_length=50, null=True, blank=True)
    seating_capacity = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    gps_coordinates = models.CharField(max_length=100, null=True, blank=True)
    google_location = models.CharField(max_length=100, null=True, blank=True)
    makhani_no = models.CharField(max_length=100, null=True, blank=True)
    meals_per_day = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    random_key = models.CharField(max_length=100)
    created_by = models.ForeignKey(Account, related_name='entity_created_by', on_delete=models.PROTECT)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='entity_modified_by', on_delete=models.PROTECT, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')
    cleaning_status_choices = [('Cleaned' , 'Cleaned') , ('Due' , 'Due') , ('Overdue' , 'Overdue')]
    cleaning_status = models.CharField(max_length=10, choices=cleaning_status_choices, default='Cleaned')
    inspection_status_choices = [('Inspected' , 'Inspected') , ('Due' , 'Due') , ('Overdue' , 'Overdue')]
    inspection_status = models.CharField(max_length=10, choices=inspection_status_choices, default='Inspected')
    modification_pending = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)

    def save(self, *args, **kwargs):
        sub_category    = self.sub_category
        subarea         = self.subarea
        self.category   = sub_category.main_category
        self.area       = subarea.area
        self.zone       = subarea.zone
        super().save(*args, **kwargs)
        return self

class EntityLog(models.Model):
    action_choices = [('Created','Created'),('Activated','Activated'),('Updated','Updated'),('UpdateApproved','UpdateApproved'),('UpdateRejected','UpdateRejected'),('Deactivated','Deactivated')]
    action_taken = models.CharField(max_length=10, choices=choices)
    action_taken_by = models.ForeignKey(Account, related_name='entitylog_account', on_delete=models.CASCADE)
    action_taken_on = models.ForeignKey(Entity, related_name='entitylog_entity', on_delete=models.CASCADE)
    # related_self_log needs to be used while Approving the update. Or else the view EntityDetailsForInspector will return the last update of user even it is approved
    related_self_log = models.ForeignKey('EntityLog', related_name='entitylog_entitylog', on_delete=models.CASCADE, null=True)
    fields_and_values = models.JSONField()
    remarks = models.CharField(max_length=1500, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

class EntityFixture(models.Model):
    entity = models.ForeignKey(Entity, related_name='entity_fixture_entity', on_delete=models.CASCADE)
    fixture = models.ForeignKey(Fixture, related_name='entity_fixture', on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=255, null=True)
    label = models.CharField(max_length=100)
    created_by = models.ForeignKey(Account, related_name='entity_fixture_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='entity_fixture_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')

    class Meta:
        ordering = ('id',)

class EntityGreaseTrap(models.Model):
    entity = models.ForeignKey(Entity, related_name='entity_grease_trap_entity', on_delete=models.CASCADE)
    grease_trap = models.ForeignKey(GreaseTrap, related_name='entity_grease_trap', on_delete=models.CASCADE)
    capacity = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=255, null=True)
    label = models.CharField(max_length=100)
    grease_trap_label = models.CharField(max_length=100, unique=True)
    cleaning_frequency = models.IntegerField(validators=[MinValueValidator(1)])
    last_cleaning_date = models.DateField()
    next_cleaning_date = models.DateField()
    foodwatch_grease_trap_id = models.CharField(max_length=100, null=True)
    created_by = models.ForeignKey(Account, related_name='entity_grease_trap_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='entity_grease_trap_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=choices, default='Active')
    entity_choices = [('Cleaned' , 'Cleaned') , ('Due' , 'Due') , ('Overdue' , 'Overdue')]
    cleaning_status = models.CharField(max_length=10, choices=entity_choices, default='Cleaned')

    class Meta:
        ordering = ('id',)

    def save(self, *args, **kwargs):
        if self.pk is None:
            try:
                max_id = EntityGreaseTrap.objects.latest('id').id + 1
            except EntityGreaseTrap.DoesNotExist:
                max_id = 1
            self.grease_trap_label  = "GT" + str("{:06d}".format(max_id))
        self.next_cleaning_date     = self.last_cleaning_date + datetime.timedelta(days=self.cleaning_frequency)
        today                       = datetime.datetime.today().date()
        if self.next_cleaning_date == today:
            self.cleaning_status = 'Due'
        elif self.next_cleaning_date < today:
            self.cleaning_status = 'Overdue'
        else:
            self.cleaning_status = 'Cleaned'
        super().save(*args, **kwargs)
        return self
        
class EntityGTCC(models.Model):
    entity = models.ForeignKey(Entity, related_name='entity_gtcc_entity', on_delete=models.CASCADE)
    gtcc = models.ForeignKey(GTCC, related_name='entity_gtcc', on_delete=models.CASCADE)
    contract_start = models.DateField(null=True)
    contract_end = models.DateField(null=True)
    reason_for_rejection = models.TextField(null=True)
    created_by = models.ForeignKey(Account, related_name='entity_gtcc_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='entity_gtcc_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    entity_gtcc_choices = [('Active' , 'Active'), ('Approval Pending' , 'Approval Pending'), ('Rejected' , 'Rejected'), ('Expired' , 'Expired')]
    status = models.CharField(max_length=20, choices=entity_gtcc_choices, default='Approval Pending')

    class Meta:
        ordering = ('id',)
        
class ServiceRequest(models.Model):
    entity = models.ForeignKey(Entity, related_name='service_request_entity', on_delete=models.CASCADE)
    entity_gtcc = models.ForeignKey(EntityGTCC, related_name='service_request_entity_gtcc', on_delete=models.CASCADE)
    vehicle = models.ForeignKey(VehicleDetail, related_name='service_request_vehicle', null=True, blank = True, on_delete=models.CASCADE)
    driver = models.ForeignKey(Account, related_name='service_request_driver', null=True, blank = True, on_delete=models.CASCADE)
    operator = models.ForeignKey(Account, related_name='service_request_operator', null=True, blank = True, on_delete=models.CASCADE)
    grease_trap_count = models.PositiveIntegerField()
    total_gallon_collected = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    dumping_vehicledetails = models.ForeignKey(VehicleEntryDetails, related_name='service_request_dumped_vehicledetails', on_delete=models.CASCADE, null=True)
    foodwatch_srid = models.CharField(max_length=100, null=True)
    created_by = models.ForeignKey(Account, related_name='service_request_created_by', null=True, blank = True, on_delete=models.CASCADE)
    collection_completion_time = models.DateTimeField(null=True)
    discharge_time = models.DateTimeField(null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='service_request_modified_by', null=True, blank = True, on_delete=models.CASCADE,)
    modified_date = models.DateTimeField(auto_now=True)
    service_request_choices = [('Initiated' , 'Initiated') , ('Assigned' , 'Assigned') , ('Processing' , 'Processing') , ('Completed' , 'Completed') , ('Discharged' , 'Discharged') , ('Canceled' , 'Canceled')]
    status = models.CharField(max_length=20, choices=service_request_choices, default='Initiated')
    initiator = models.CharField(max_length=20, default='FGW')
    qr_scan_location = models.CharField(max_length=500, null=True)
    publish_location = models.CharField(max_length=500, null=True)

    class Meta:
        ordering = ('id',)

class ServiceRequestDetail(models.Model):
    service_request = models.ForeignKey(ServiceRequest, related_name='service_request', on_delete=models.CASCADE)
    grease_trap = models.ForeignKey(EntityGreaseTrap, related_name='service_request_grease_trap', on_delete=models.CASCADE)
    modified_by = models.ForeignKey(Account, related_name='service_request_detail_modified_by', null=True, blank = True, on_delete=models.CASCADE,)
    modified_date = models.DateTimeField(auto_now=True)
    choices1 = [('Perfect' , 'Perfect'), ('Good' , 'Good'), ('Old' , 'Old') , ('Damaged' , 'Damaged') , ('Unavailable' , 'Unavailable'), ('Not set', 'Not set')]
    choices2 = [('Light' , 'Light'), ('Moderate' , 'Moderate'), ('Heavy' , 'Heavy') , ('Solid' , 'Solid'), ('Not set', 'Not set')]
    grease_trap_condtion = models.CharField(max_length=20, choices=choices1, default = 'Not set')
    waste_contents = models.CharField(max_length=20, choices=choices2, default = 'Not set')
    cover_condition = models.CharField(max_length=20, choices=choices1, default = 'Not set')
    buffle_wall_condition = models.CharField(max_length=20, choices=choices1, default = 'Not set')
    outlet_elbow_condition = models.CharField(max_length=20, choices=choices1, default = 'Not set')
    service_request_detail_choices = [('Pending' , 'Pending') , ('Completed' , 'Completed') , ('PartiallyCompleted' , 'PartiallyCompleted'), ('Skipped' , 'Skipped')]
    status = models.CharField(max_length=20, choices=service_request_detail_choices, default='Pending')

    class Meta:
        ordering = ('id',)

class ServiceRequestDetailImage(models.Model):
    service_request_detail =  models.ForeignKey(ServiceRequestDetail, related_name='service_request_detail', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='service_request')
    image_type_choices = [('Before' , 'Before') , ('After' , 'After')]
    image_type = models.CharField(max_length=10, choices=image_type_choices)
    uploaded_by = models.ForeignKey(Account, related_name='service_request_image_created_by', on_delete=models.CASCADE)
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
            ordering = ('id',)

class ServiceRequestLog(models.Model):
    service_request = models.ForeignKey(ServiceRequest, related_name='log_service_request', on_delete=models.CASCADE)
    vehicle = models.ForeignKey(VehicleDetail, related_name='log_vehicle', null=True, blank = True, on_delete=models.CASCADE)
    driver = models.ForeignKey(Account, related_name='log_driver', null=True, blank = True, on_delete=models.CASCADE)
    type  = models.CharField(max_length=50)
    log  = models.CharField(max_length=255)
    created_by = models.ForeignKey(Account, related_name='log_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
