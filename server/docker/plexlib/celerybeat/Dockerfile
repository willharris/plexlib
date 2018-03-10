FROM plexlib_celery:latest

CMD [ "celery", "-A", "plexlib.tasks.celery", \
                "beat", \
                "--loglevel", "INFO", \
                "--schedule", "/tmp/celerybeat-schedule.db", \
                "--pidfile", "/tmp/celerybeat.pid" ]
