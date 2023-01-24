from apscheduler.schedulers.background import BackgroundScheduler
from .job import update_notification_status

def start():
	scheduler = BackgroundScheduler(timezone="Asia/Dubai")
	scheduler.add_job(update_notification_status, 'cron', second='*')
	scheduler.start()