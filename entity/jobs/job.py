from django.utils import timezone
from entity.models import EntityGreaseTrap
from django.db.models import Q

def update_entity_grease_trap_cleaning_status():
    today        = timezone.now().date()
    grease_traps = EntityGreaseTrap.objects.filter((Q(cleaning_status='Cleaned') | Q(cleaning_status='Due')), next_cleaning_date__lte=today)
    for grease_trap in grease_traps:
        if grease_trap.next_cleaning_date == today:
            grease_trap.cleaning_status = 'Due'
        else:
            grease_trap.cleaning_status = 'Overdue'
        grease_trap.save()
            

