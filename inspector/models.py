from django.db import models
from masters.models import Area, GreaseTrap
from entity.models import Entity, EntityGreaseTrap
from users.models import Account

class EntityInspection(models.Model):
    inspection_id = models.CharField(max_length=100)
    entity = models.ForeignKey(Entity, related_name='inspection_entity', on_delete=models.CASCADE)
    establishment_name = models.CharField(max_length=255)
    makhani_no = models.CharField(max_length=100, null=True, blank=True)
    trade_license_no = models.CharField(max_length=100, null=True, blank=True)
    entity_location = models.CharField(max_length=255, null=True, blank=True)
    phone_no = models.CharField(max_length=50, null=True, blank=True)
    meals_per_day = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    seating_capacity = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    area = models.ForeignKey(Area, related_name='inspection_entity_area', on_delete=models.PROTECT)
    remarks = models.TextField(null=True)
    is_inspection_follow_up = models.BooleanField()
    is_report_to_dm = models.BooleanField()
    inspection_status_choices = [('Completed' , 'Completed') , ('Pending' , 'Pending')]
    inspection_status = models.CharField(max_length=10, choices=inspection_status_choices, default='Pending')
    status_choices = [('Active' , 'Active') , ('Disabled', 'Disabled'), ('Deleted', 'Deleted')]
    status = models.CharField(max_length=20, choices=status_choices, default='Active')
    created_by = models.ForeignKey(Account, related_name='inspection_entity_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='inspection_entity_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            try:
                max_id = EntityInspection.objects.latest('id').id + 1
            except EntityInspection.DoesNotExist:
                max_id = 1
            self.inspection_id  = "IR" + str("{:06d}".format(max_id))
        super().save(*args, **kwargs)
        return self

class EntityInspectionImages(models.Model):
    entity_inspection = models.ForeignKey(EntityInspection, related_name='inspection_image_entity', on_delete=models.CASCADE)
    image = models.ImageField()
    image_type = models.CharField(max_length=10)
    created_date = models.DateTimeField(auto_now_add=True)

class EntityGreaseTrapInspection(models.Model):
    entity_inspection = models.ForeignKey(EntityInspection, related_name='inspection_entity_detail', on_delete=models.CASCADE)
    grease_trap = models.ForeignKey(GreaseTrap, related_name='inspection_entity_grease_trap', on_delete=models.CASCADE)
    entity_grease_trap = models.ForeignKey(EntityGreaseTrap, related_name='inspection_entity_grease_trap', on_delete=models.CASCADE)
    capacity = models.DecimalField(max_digits=6, decimal_places=2)
    current_cleaning_frequency = models.IntegerField()
    required_cleaning_frequency = models.IntegerField()
    last_cleaning_date = models.DateField()
    inspection_status_choices = [('Completed' , 'Completed') , ('Pending' , 'Pending'), ('Skipped' , 'Skipped'), ('Reinspection' , 'Reinspection')]
    inspection_status = models.CharField(max_length=15, choices=inspection_status_choices, default='Pending')
    choices1 = [('Perfect' , 'Perfect'), ('Good' , 'Good'), ('Old' , 'Old') , ('Damaged' , 'Damaged') , ('Unavailable' , 'Unavailable'), ('Not set', 'Not set')]
    grease_trap_condtion = models.CharField(max_length=20, choices=choices1, default = 'Not set')
    cover_condition = models.CharField(max_length=20, choices=choices1, default = 'Not set')
    created_by = models.ForeignKey(Account, related_name='inspection_entity_grease_trap_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(Account, related_name='inspection_entity_grease_trap_modified_by', on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)

class EntityGreaseTrapInspectionImages(models.Model):
    entity_grease_trap_inspection = models.ForeignKey(EntityGreaseTrapInspection, related_name='entity_grease_trap_inspection_image', on_delete=models.CASCADE)
    image = models.ImageField()
    image_type_choices = [('Before' , 'Before') , ('After' , 'After')]
    image_type = models.CharField(max_length=10, choices=image_type_choices)
    created_date = models.DateTimeField(auto_now_add=True)

