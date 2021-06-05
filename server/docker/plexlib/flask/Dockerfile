FROM alpine:latest

RUN apk add --no-cache python3 py3-pip uwsgi uwsgi-python3

RUN adduser -h /home/app -D plexlib

WORKDIR /home/app

COPY ./server/docker/plexlib/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./src ./src
RUN chown -R plexlib:plexlib /home/app

ENV PLEXLIB_LOGDIR ""
ENV PLEXLIB_MOVIES_ROOT "/mnt/video/movies"
ENV PLEXLIB_TVSHOWS_ROOT "/mnt/video/tv_shows"

WORKDIR /home/app/src

USER plexlib

CMD [ "uwsgi", "--master", \
               "--socket", "0.0.0.0:3031", \
               "--enable-threads", \
               "--plugins", "python", \
               "--processes", "2", \
               "--threads", "2", \
               "--module", "run:app" ]
