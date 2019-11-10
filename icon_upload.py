#!/usr/bin/env python

# Upload files named on ARGV as Slack emoji.
# https://github.com/smashwilson/slack-emojinator

from __future__ import print_function

import argparse
import os
import re
from time import sleep

from bs4 import BeautifulSoup
import requests


from utils import dprint

try:
    raw_input
except NameError:
    raw_input = input

URL_CUSTOMIZE = "https://{team_name}.slack.com/customize/emoji"
URL_ADD = "https://{team_name}.slack.com/api/emoji.add"
URL_LIST = "https://{team_name}.slack.com/api/emoji.adminList"

API_TOKEN_REGEX = r'.*(?:\"?api_token\"?):\s*\"([^"]+)\".*'
API_TOKEN_PATTERN = re.compile(API_TOKEN_REGEX)

class ParseError(Exception):
    pass


class Uploader(object):

    def __init__(self, token, team_name, cookie):
        self.team_name = team_name
        self.token = token
        self.cookie = cookie

    def _session(self):
        assert self.cookie, "Cookie required"
        assert self.team_name, "Team name required"
        session = requests.session()
        session.headers = {'Cookie': self.cookie}
        session.url_customize = URL_CUSTOMIZE.format(team_name=self.team_name)
        session.url_add = URL_ADD.format(team_name=self.team_name)
        session.url_list = URL_LIST.format(team_name=self.team_name)
        session.api_token = self._fetch_api_token(session)
        return session

    def _fetch_api_token(self, session):
        # Fetch the form first, to get an api_token.
        r = session.get(session.url_customize)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        all_script = soup.findAll("script")
        for script in all_script:
            for line in script.text.splitlines():
                if 'api_token' in line:
                    # api_token: "xoxs-12345-abcdefg....",
                    # "api_token":"xoxs-12345-abcdefg....",
                    match_group = API_TOKEN_PATTERN.match(line.strip())
                    if not match_group:
                        raise ParseError(
                            "Could not parse API token from remote data! "
                            "Regex requires updating."
                        )

                    return match_group.group(1)

        raise ParseError("No api_token found in page")


    def upload(self, icon_path_list):

        dprint('Upload start')

        session = self._session()
        existing_emojis = self.get_current_emoji_list(session)
        uploaded = 0
        skipped = 0
        for icon_path in icon_path_list:
            print("Processing {}.".format(icon_path))
            file_name = os.path.basename(icon_path)
            emoji_name, ext = os.path.splitext(file_name)
            if emoji_name in existing_emojis:
                print("Skipping {}. Emoji already exists".format(emoji_name))
                skipped += 1
            else:
                self.add_emoji(session, emoji_name, icon_path)
                print("{} upload complete.".format(icon_path))
                uploaded += 1
        print('\nUploaded {} emojis. ({} already existed)'.format(uploaded, skipped))
        dprint('Upload finish')


    def get_current_emoji_list(self, session):
        page = 1
        result = []
        while True:
            data = {
                'query': '',
                'page': page,
                'count': 1000,
                'token': session.api_token
            }
            resp = session.post(session.url_list, data=data)
            resp.raise_for_status()
            response_json = resp.json()

            result.extend(map(lambda e: e["name"], response_json["emoji"]))
            if page >= response_json["paging"]["pages"]:
                break

            page = page + 1
        return result


    def add_emoji(self, session, emoji_name, file_path):
        data = {
            'mode': 'data',
            'name': emoji_name,
            'token': session.api_token
        }

        i = 0
        while True:
            i += 1
            with open(file_path, 'rb') as f:
                files = {'image': f}
                resp = session.post(session.url_add, data=data, files=files, allow_redirects=False)

                if resp.status_code == 429:
                    wait = 2**i
                    print("429 Too Many Requests!, sleeping for %d seconds" % wait)
                    sleep(wait)
                    continue

            resp.raise_for_status()

            # Slack returns 200 OK even if upload fails, so check for status.
            response_json = resp.json()
            if not response_json['ok']:
                print("Error with uploading %s: %s" % (emoji_name, response_json))

            break

