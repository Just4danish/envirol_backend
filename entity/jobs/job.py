from django.utils import timezone
from entity.models import EntityGreaseTrap
from django.db.models import Q
from foodwatch.views import submit_service_request
import json

def update_entity_grease_trap_cleaning_status():
    today        = timezone.now().date()
    grease_traps = EntityGreaseTrap.objects.filter((Q(cleaning_status='Cleaned') | Q(cleaning_status='Due')), next_cleaning_date__lte=today).select_related('entity')
    for grease_trap in grease_traps:
        if grease_trap.next_cleaning_date == today:
            grease_trap.cleaning_status = 'Due'
            entity_foodwatch_id = grease_trap.entity.foodwatch_id
            if entity_foodwatch_id is not None:
                api_response    = submit_service_request(entity_foodwatch_id, grease_trap.grease_trap_label)
                response        = api_response['data']
                api_log         = api_response['api_log']
                if response.status_code == 200:
                    json_object = json.loads(response.text)
                    if json_object['ResultCode'] == 200:
                        api_log.status = 'Success'
                    else:
                        api_log.status = 'Failed'
                    api_log.response      = json_object
                else:
                    api_log.response    = "Failed to connect"
                    api_log.status      = 'Failed'
                api_log.response_time = timezone.now()
                api_log.save()
        else:
            grease_trap.cleaning_status = 'Overdue'
        grease_trap.save()
            

