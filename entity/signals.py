from django.db.models import signals
from django.dispatch import receiver
from .models import EntityGreaseTrap, ServiceRequestDetail
from foodwatch.views import submit_service_request, tag_equipment, save_api_log

@receiver(signals.post_save, sender = EntityGreaseTrap) 
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

@receiver(signals.post_save, sender = EntityGreaseTrap) 
def call_food_watch_tag_equipment_api(sender, instance, created, **kwargs):
    if created:
        entity_foodwatch_id = instance.entity.foodwatch_id
        if entity_foodwatch_id is not None:
            api_response    = tag_equipment(entity_foodwatch_id, instance.grease_trap_label)
            api_log         = save_api_log(api_response)
            if api_log['status']:
                instance.foodwatch_grease_trap_id = api_log['result']
                instance.save()

@receiver(signals.post_save, sender = ServiceRequestDetail) 
def call_food_watch_sr_api(sender, instance, created, **kwargs):
    if created:
        service_request     = instance.service_request
        entity              = service_request.entity
        initiator           = service_request.initiator
        entity_foodwatch_id = entity.foodwatch_id
        if entity_foodwatch_id is not None and initiator == 'FGW':
            grease_trap         = instance.grease_trap
            grease_trap_label   = grease_trap.grease_trap_label
            api_response    = submit_service_request(entity_foodwatch_id, grease_trap_label)
            api_log         = save_api_log(api_response)
            if api_log['status']:
                service_request.foodwatch_srid = api_log['result']
                service_request.save()