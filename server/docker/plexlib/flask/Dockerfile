FROM alpine:latest

RUN apk add --no-cache python py-pip uwsgi uwsgi-python

RUN adduser -h /home/flask -D flask

WORKDIR /home/flask

COPY ./server/docker/plexlib/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

USER flask

COPY ./src ./src

ENV REDIS_URL "redis://redis:6379/0"
ENV CELERY_BROKER_URL "amqp://plexlib:plexlib@rabbitmq/plexlib"
ENV PLEX_MOVIES_ROOT "/mnt/video/movies"
ENV PLEX_TVSHOWS_ROOT "/mnt/video/tv_shows"

WORKDIR /home/flask/src

EXPOSE 3031

CMD [ "uwsgi", "--master", \
               "--socket", "0.0.0.0:3031", \
               "--enable-threads", \
               "--plugins", "python", \
               "--processes", "2", \
               "--threads", "2", \
               "--module", "run:app" ]
