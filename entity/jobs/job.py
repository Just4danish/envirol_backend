from django.utils import timezone
from entity.models import EntityGreaseTrap, ServiceRequest, ServiceRequestDetail, ServiceRequestLog
from django.db.models import Q

def update_entity_grease_trap_cleaning_status():
    today        = timezone.now().date()
    grease_traps = EntityGreaseTrap.objects.filter((Q(cleaning_status='Cleaned') | Q(cleaning_status='Due')), next_cleaning_date__lte=today).select_related('entity')
    for grease_trap in grease_traps:
        sr_required = True
        if grease_trap.next_cleaning_date == today:
            grease_trap.cleaning_status = 'Due'
        else:
            if grease_trap.cleaning_status == 'Due':
                sr_required = False
            grease_trap.cleaning_status = 'Overdue'
        pending_grease_trap_sr = ServiceRequestDetail.objects.filter(grease_trap=grease_trap, status='Pending').exists()
        if sr_required and not pending_grease_trap_sr:
            entity              = grease_trap.entity
            active_gtcc_detail  = entity.active_gtcc_detail
            if active_gtcc_detail.status == 'Active':
                service_request = ServiceRequest.objects.create(
                    entity = entity, 
                    entity_gtcc = active_gtcc_detail, 
                    grease_trap_count = 1,
                    created_by_id = 1
                )
                ServiceRequestDetail.objects.create(
                    service_request = service_request,
                    grease_trap = grease_trap
                )
                ServiceRequestLog.objects.create(
                    service_request = service_request,
                    type = "Initiated",
                    log = "Job initiated from "+entity.establishment_name,
                    created_by_id = 1
                )
        grease_trap.save()
            

