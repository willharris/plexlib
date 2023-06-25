#!/usr/bin/env python3
"""
Parse an email sent from Synology DSM DownloadStation and biff the PlexLib server.

To use, set then environment variable PLEXLIB_BASE_URL to point to your PlexLib server, and
provide the contents of the email on stdin. To echo the contents of the input to stdout,
(for example for use with procmail filter mode) call with -e

Command line:
$ PLEXLIB_BASE_URL=http://localhost:8888 syno_media_biff.py < input-email.eml

Procmail recipe:
:0 fbw
* ^Subject:.*download task completed
| PLEXLIB_BASE_URL=http://localhost:8888 syno_media_biff.py -e


"""
import os
import re
import sys

from urllib.parse import urlencode
from urllib.request import urlopen


try:
    PLEXLIB_URL = os.environ['PLEXLIB_BASE_URL']
except KeyError:
    print('Please specify PLEXLIB_BASE_URL in the environment')
    sys.exit(1)


def getline(echo):
    line = sys.stdin.readline()
    if echo:
        sys.stdout.write(line)
    return line


def main(echo=False):
    videofile = None
    location = None

    line = getline(echo)
    while line:
        if re.match(r'^Your BT download task', line):
            getline(echo)
            line = getline(echo)
            if re.match(r'^File:$', line):
                # Avoid "crazy" data longer than 256 bytes (DoS)
                videofile = getline(echo).rstrip()[:256]
                getline(echo)
                line = getline(echo)
                if re.match(r'^Location:$', line):
                    location = getline(echo).rstrip()
                    break
        line = getline(echo)

    # if echoing, process any remaining input lines
    if echo:
        while getline(True):
            pass

    if location == 'Video' and videofile:
        data = urlencode([('name', videofile)])
        url = '%s/update/from_name/' % PLEXLIB_URL
        print(url)
        print(data)
        try:
            conn = urlopen(url, data.encode("utf8"))
            print('Result:')
            print(conn.read())
        except Exception as ex:
            print('Error calling PlexLib: %s' % ex)


if __name__ == '__main__':
    if sys.argv[-1] == '-e':
        main(True)
    else:
        main()
