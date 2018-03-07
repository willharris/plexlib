FROM alpine:latest

RUN apk add --no-cache python py-pip

RUN adduser -h /home/celery -D celery

WORKDIR /home/celery

COPY ./server/docker/plexlib/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

USER celery

COPY ./src ./src

ENV REDIS_URL "redis://redis:6379/0"
ENV CELERY_BROKER_URL "amqp://plexlib:plexlib@rabbitmq/plexlib"
ENV PLEX_MOVIES_ROOT "/mnt/video/movies"
ENV PLEX_TVSHOWS_ROOT "/mnt/video/tv_shows"

WORKDIR /home/celery/src

CMD [ "celery", "-A", "plexlib.tasks.celery", \
                "worker", \
                "--concurrency", "1", \
                "--loglevel", "INFO" ]
