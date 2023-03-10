from django.db import models
from masters.models import SubCategory, SubArea, Zone, Area, MainCategory
from users.models import Account

class FoodwatchEntity(models.Model):
    foodwatch_id = models.IntegerField()
    business_id = models.IntegerField(null=True)
    name_of_establishment = models.CharField(max_length=100)
    active_contact_person = models.ForeignKey(Account, related_name='fogwatch_active_contact_person', on_delete=models.PROTECT, null=True)
    license_nr = models.CharField(max_length=100, null=True)
    gtcc_foodwatch_id = models.IntegerField(null=True)
    entity_class_id = models.IntegerField(null=True)
    entity_class = models.CharField(max_length=100, null=True)
    fogwatch_category = models.ForeignKey(MainCategory, related_name='fogwatch_category', on_delete=models.PROTECT, null=True)
    fogwatch_sub_category = models.ForeignKey(SubCategory, related_name='fogwatch_sub_category', on_delete=models.PROTECT, null=True)
    address = models.TextField()
    po_box = models.IntegerField(null=True)
    office_line = models.CharField(max_length=20,null=True)
    office_email = models.EmailField(null=True)
    makani_nr = models.IntegerField(null=True)
    latitue_longitude = models.CharField(max_length=100, null=True)
    category_id = models.IntegerField(null=True)
    category = models.CharField(max_length=100, null=True)
    sub_category_id = models.IntegerField(null=True)
    sub_category = models.CharField(max_length=100, null=True)
    website_url = models.URLField(null=True)
    office_mobile = models.CharField(max_length=20, null=True)
    qr_code = models.TextField(null=True)
    uae_region_id = models.IntegerField(null=True)
    uae_region_name = models.CharField(max_length=100, null=True)
    fogwatch_zone = models.ForeignKey(Zone, related_name='fogwatch_zone', on_delete=models.PROTECT, null=True)
    fogwatch_area = models.ForeignKey(Area, related_name='fogwatch_area', on_delete=models.PROTECT, null=True)
    fogwatch_sub_area = models.ForeignKey(SubArea, related_name='fogwatch_sub_area', on_delete=models.PROTECT, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(Account, related_name='foodwatch_entity_modified_by', on_delete=models.PROTECT, null=True)
    is_convertable = models.BooleanField(default=False)
    status_choices = [('Pending', 'Pending'), ('Synced', 'Synced'), ('Converted', 'Converted'), ('Deleted', 'Deleted')]
    status = models.CharField(max_length=10, choices=status_choices, default='Pending')

    def save(self, *args, **kwargs):
        fogwatch_sub_category    = self.fogwatch_sub_category
        fogwatch_sub_area        = self.fogwatch_sub_area
        if fogwatch_sub_category:
            self.fogwatch_category   = fogwatch_sub_category.main_category
        if fogwatch_sub_area:
            self.fogwatch_area       = fogwatch_sub_area.area
            self.fogwatch_zone       = fogwatch_sub_area.zone
        super().save(*args, **kwargs)
        return self

class APILog(models.Model):
    url = models.URLField()
    api_class = models.CharField(max_length=100)
    call_time = models.DateTimeField(auto_now_add=True)
    response_time = models.DateTimeField(null=True)
    response = models.JSONField(null=True)
    status_choices = [('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')]
    status = models.CharField(max_length=10, choices=status_choices, default='Pending')
