from django.db.models import signals
from django.dispatch import receiver
from .models import EntityGreaseTrap

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