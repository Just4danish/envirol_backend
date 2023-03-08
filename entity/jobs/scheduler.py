from apscheduler.schedulers.background import BackgroundScheduler
from .job import update_entity_grease_trap_cleaning_status

def start():
	scheduler = BackgroundScheduler(timezone="Asia/Dubai")
	# scheduler.add_job(update_entity_grease_trap_cleaning_status, 'cron', hour=0, minute=0, second=0)
	scheduler.add_job(update_entity_grease_trap_cleaning_status, 'cron', hour=16, minute=34, second=0)
	scheduler.start()