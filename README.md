# PlexLib

This is a small Flask-based web application to allow on-demand updating of a [Plex](https://www.plex.tv) library, sending an email notification when new media has been added.

#### Motivation

My Plex server runs on a Mac Mini, with the actual media held on a Synology NAS, neither of which is a computational powerhouse. Having Plex randomly initiate library update scans can quite negatively affect the server's performance, leading to playback issues if I happen to be watching something at the same time. In addition, as the media is stored on a network share, Plex cannot reliably identify when new media has been added. I have therefore disabled any of Plex's automatic library scanning and updating.

This has left me with the problem of how to get media properly added to Plex in a timely fashion (i.e. so that I don't have to manually run a scan). I wanted to have a way to get Plex to update the library on-demand when new media has been added. Since I receive an email from the NAS when a download has completed, I figured I could use procmail or something to ping a webservice and trigger the updating on demand.

Also, I wanted to play around with Flask!

## Setup

The system has been implemented with the following setup in mind:

* Flask running under uWSGI behind nginx
* Redis as a simple key/value store to keep track of when updates have been performed, and which media has been added to the system
* Celery with RabbitMQ as an async task processor  

### Installation

1. Install Redis. By default, the system uses the following access URL: `redis://localhost:6379/1`.
2. Install RabbitMQ. By default, the system uses the following access URL: `amqp://plexlib:plexlib@localhost/plexlib`
so if you want to use those values, you'll need to set up RabbitMQ appropriately.
3. Create a virtualenv called `plexlib`, and use `pip` to install the requirements from `requirements.txt`
4. At the top of the project, create a directory named `envs`, and create the following files with the appropriate content. Alternatively, variables with these names can be specified directly in the environment for both Flask and Celery.
    * `FLASK_ADMINS`: a python list containing email addresses that should receive notifications in the event Flask throws an exception. Example: `['postmaster@yourdomain.com']`
    * `FLASK_CONFIG`: (optional) set this to `ProdConfig` in a production environment.
    * `FLASK_DEBUG`: (optional) set this to `False` for a "production" environment.
    * `FLASK_MAIL_SERVER`: the hostname of an SMTP server which will accept mails. If you need more control over the SMTP settings, you can configure any of the usual Flask-Mail settings by creating appropriate files prefixed with `FLASK_`, e.g. `FLASK_USE_TLS`
    * `NOTIFICATION_RECIPIENT`: an email address that will receive emails when the system detects that new media has been added to Plex.
    * `PLEX_TOKEN`: A valid authentication token for accessing your Plex server. See the [Plex Documentation](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) for information on how to find this token.
    * `PLEX_URL`: the URL to your Plex server.
    * `PLEX_MOVIES_ROOT`: (optional) The root directory for your Plex movie files. Default: `/Volumes/Video/Movies`.
    * `PLEX_TVSHOWS_ROOT`: (optional) The root directory for your Plex TV show files. Default: `/Volumes/Video/TV`.
    * `REDIS_URL`: (optional) If you want to use a different access URL to the one above.
    * `CELERY_BROKER_URL`: (optional) If you want to use a different access URL to the one above.
    * (optional) Any file created with the prefix `FLASK_` will be added to the Flask configuration.
    * (optional) Have a look at `src/plexlib/config.py` for other configuration parameters.
5. Run uWSGI in Emperor mode, pointing it at the directory containing the app configurations:
    
    `uwsgi --emperor ./server/uwsgi`

6. Create an nginx virtual host and point it at your Flask socket file. A sample configuration can be found at `server/nginx/plexlib`.

### Docker

A basic `docker-compose` configuration is provided at `servers/docker/plexlib/docker-compose.yml`. Before bringing up the system, you should create the necessary environment files as described in step 4 of the instructions above - these will be mounted as read-only volumes in the `flask` and `celery` containers. *Note:* the `REDIS_URL` and `CELERY_BROKER_URL` variables should not be defined, as these are defined in the Dockerfiles so as to use the containerized services.

The following command will build the images and bring up the containers:

`docker-compose -f server/docker/plexlib/docker-compose.yml up -d`

The Docker configuration consists of the following five containers (one for each basic service) and expose the following ports on `localhost`:

* `flask`
* `celery`
* `nginx`: port 8888, for normal HTTP access
* `redis`: port 6379, for access via `redis-cli` etc.
* `rabbitmq`: port 15672, for access to the RabbitMQ web management console

Sample output from `docker ps` is shown below:
```
CONTAINER ID        IMAGE                        COMMAND                  CREATED             STATUS              PORTS                                                                     NAMES
c2d050927216        nginx:alpine                 "nginx -g 'daemon of…"   18 minutes ago      Up 18 minutes       80/tcp, 0.0.0.0:8888->8888/tcp                                            plexlib_nginx_1
e39e7daf89b0        plexlib_celery               "celery -A plexlib.t…"   18 minutes ago      Up 18 minutes                                                                                 plexlib_celery_1
e6c03fa787c4        plexlib_flask                "uwsgi --master --so…"   18 minutes ago      Up 18 minutes       3031/tcp                                                                  plexlib_flask_1
0d37b0ea6279        redis:alpine                 "docker-entrypoint.s…"   2 hours ago         Up 18 minutes       0.0.0.0:6379->6379/tcp                                                    plexlib_redis_1
09d8b3797e2b        rabbitmq:management-alpine   "docker-entrypoint.s…"   19 hours ago        Up 18 minutes       4369/tcp, 5671-5672/tcp, 15671/tcp, 25672/tcp, 0.0.0.0:15672->15672/tcp   plexlib_rabbitmq_1
```

#### Development

To use Docker during development, you can run `docker-compose` and include the provided `dev` file:

`docker-compose -f server/docker/plexlib/docker-compose.yml -f server/docker/plexlib/docker-compose.dev.yml up -d`

This will replace the production `uwsgi` configuration in the `flask` container with a standard Flask development server, and mount the `src` and `web` directories in the container so that source code changes will be detected. Flask's standard port 5000 will also be exposed.

*Tip*
To make working with `docker-compse` simpler, without having to specify the files on the commandline, you can rename `docker-compose.dev.yml` to `docker-compose.override.yml`. If you run `docker-compse` from the `plexlib` directly, it will then pick up the override file automatically:

```bash
cd server/docker/plexlib
docker-compose up -d
``` 

## Usage

The system can be called two ways (assuming you are running on port 8888 as per the sample nginx configuration):

* Make a GET request to `http://<your server>:8888/update/<section name>/`

For example, if you wanted to update the "TV Shows" section, you could execute the following:

`curl http://<your server>:8888/update/TV%20Shows/`

* Make a POST request to `http://<your server>:8888/update/from_name/`, setting the value of `name` to a file name that can be found in your videos.

For example if you had a file named "My Fancy Show S07E22 Awesome Episode.mp4", you could execute the following:

`curl -d 'name=My Fancy Show S07E22 Awesome Episode.mp4' http://<your server>:8888/update/from_name/`

### Homepage

The PlexLib homepage provides a simple interface through which you can check that the server is working properly, and has a connection to your configured Plex Media Server. In addition, you can trigger an update for any of your library sections by clicking on the corresponding link.

To navigate to the homepage, assuming your server is running at `localhost:8888`, just point your browser to http://localhost:8888/.

### Procmail Usage

As the original goal of this project was to automatically process emails from a Synology DiskStation, a sample [biff-type](https://en.wikipedia.org/wiki/Biff) utility is included at `src/syno_media_biff.py`, which can be used with procmail and a standard Python installation (no additional packages needed).

To use the biffer, add a rule to your procmail ruleset:

    :0 fbw
    * ^Subject:.*download task completed
    | PLEXLIB_BASE_URL=http://<your server>:8888 syno_media_biff.py -e

The biffer will process the mail on standard input, and if it finds a new media file in the email, will call the PlexLib instance configured at `PLEXLIB_BASE_URL`. By using the `-e` option, the original content of the mail will be echoed to standard output, so you can deliver the mail as usual. The biffer adds additional information about the result of the PlexLib call to the end of the message.

## Todo

* <s>Dockerization</s>
* Reconnect listener if connection lost
* Exception handling in celery tasks
* Add some launchctl plists for running on MacOS
* Tests
* Compatibility with Python 3
