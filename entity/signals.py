from django.db.models import signals
from django.dispatch import receiver
from .models import EntityGreaseTrap, ServiceRequestDetail
from foodwatch.views import submit_service_request, tag_equipment, save_api_log

@receiver(signals.post_save, sender=EntityGreaseTrap) 
def update_entity_cleaning_status(sender, instance, created, **kwargs):
    entity = instance.entity
    if instance.cleaning_status == 'Overdue':
        entity.cleaning_status = 'Overdue'
    else:
        entity_overdue_count = sender.objects.filter(entity=entity, cleaning_status='Overdue').count()
        if entity_overdue_count == 0:
            entity_due_count = sender.objects.filter(entity=entity, cleaning_status='Due').count()
            if entity_due_count == 0:
                entity.cleaning_status = 'Cleaned'
            else:
                entity.cleaning_status = 'Due'
        else:
            entity.cleaning_status = 'Overdue'
    entity.save()

@receiver(signals.post_save, sender=EntityGreaseTrap) 
def call_food_watch_tag_equipment_api(sender, instance, created, **kwargs):
    if created:
        entity_foodwatch_id = instance.entity.foodwatch_id
        if entity_foodwatch_id is not None:
            api_response    = tag_equipment(entity_foodwatch_id, instance.grease_trap_label)
            save_api_log(api_response)

# @receiver(signals.post_save, sender=ServiceRequestDetail) 
# def call_food_watch_sr_api(sender, instance, created, **kwargs):
#     if created:
#         service_request     = instance.service_request
#         entity              = service_request.entity
#         entity_foodwatch_id = entity.foodwatch_id
#         if entity_foodwatch_id is not None:
#             pass
            # grease_traps = instance.service_request
            # for grease_traps
            # api_response    = submit_service_request(entity_foodwatch_id, grease_trap.grease_trap_label)
            # save_api_log(api_response)