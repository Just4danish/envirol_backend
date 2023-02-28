from django.utils import timezone
from masters.models import Notification, Gate

def update_notification_status():
    notification = Notification.objects.exclude(status = 'Expired').first()
    if notification != None:
        current_time = timezone.now()
        if notification.status == 'Active':
            if notification.end_time <= current_time:
                notification.status = 'Expired'
                notification.save()
        elif notification.status == 'Queued':
            if notification.start_time >= current_time:
                notification.status = 'Active'
                notification.save()

def update_gate_remote_status():
    gates = Gate.objects.filter(remote_status='Online', last_query_time__isnull=False)
    for gate in gates:
        last_query_time     = gate.last_query_time
        time_diff           = timezone.now() - last_query_time
        time_diff_in_sec    = time_diff.total_seconds()
        time_diff_in_hours  = time_diff_in_sec / (60 * 60)
        if time_diff_in_hours >= 1:
            gate.remote_status = 'Offline'
            gate.save()
