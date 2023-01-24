from apscheduler.schedulers.background import BackgroundScheduler
from .job import update_entity_grease_trap_cleaning_status

def start():
	scheduler = BackgroundScheduler(timezone="Asia/Dubai")
	scheduler.add_job(update_entity_grease_trap_cleaning_status, 'cron', second=1)
	scheduler.start()