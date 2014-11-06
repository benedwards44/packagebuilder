web: gunicorn packagebuilder.wsgi --workers $WEB_CONCURRENCY
worker: celery -A buildpackage.tasks worker -B --loglevel=info