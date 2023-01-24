from django.utils import timezone
from masters.models import Notification

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

