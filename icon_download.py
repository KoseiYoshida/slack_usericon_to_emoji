import json
import os
from os.path import join, dirname
import urllib.error
import urllib.request


import requests
from dotenv import load_dotenv
import mojimoji
from pykakasi import kakasi


from utils import dprint


USERLIST_GETURL_BASE = 'https://slack.com/api/users.list?token='



class Downloader(object):

    def __init__(self, token):
        self.token = token
        

    def get_userslist_json(self):
        headers = {'content-type': 'application/json'}
        res = requests.get(USERLIST_GETURL_BASE + self.token, headers)
        users_list = res.json()
        users_list = users_list['members']
        return users_list


    def download_file(self, url, dst_path):
        try:
            with urllib.request.urlopen(url) as web_file, open(dst_path, 'wb') as local_file:
                local_file.write(web_file.read())
                return True
        except urllib.error.URLError as e:
            print('download faile {}, error = {e}'.format(dst_path,e))
            return False


    def fix_name_style(self, name):
            
        jpn2romaji = kakasi()
        jpn2romaji.setMode('J', 'a')
        jpn2romaji.setMode('K', 'a')
        jpn2romaji.setMode('H', 'a')
        k2r_conv = jpn2romaji.getConverter()
        fixed_name = k2r_conv.do(name)

        fixed_name = mojimoji.zen_to_han(fixed_name)


        fixed_name = fixed_name.replace(".", "")
        fixed_name = fixed_name.replace(' ', '')

        return fixed_name


    def is_target_member(self, member):

        if member['is_bot']:
            return False

        # デフォルトで参加しているSlackBotは'is_bot'が何故かFalseになっているため、名前ではじく
        if member['name'] == 'slackbot':
            return False

        if member['deleted'] == 'True':
            return False

        return True


    def can_get_imageURL_from(self, profile):	

        if not 'image_original' in profile.keys():
            return False

        return True


    def download(self, save_directory_name):

        if not os.path.exists(save_directory_name):
            os.mkdir(save_directory_name)

        members_list = self.get_userslist_json()

        saved_file_path_list = []

        dprint('Download start, save to ./{save_folder}'.format(save_folder = save_directory_name))
        for member in members_list:

            if not self.is_target_member(member):
                continue

            member_prof = member['profile']

            name = member_prof['display_name'].lower()
            name = self.fix_name_style(name)

            if not self.can_get_imageURL_from(member_prof):
                continue

            image_url = member_prof['image_original']
            _, ext = os.path.splitext(image_url)

            saved_file_path = './' + save_directory_name + os.sep + name + ext
            is_save_success = self.download_file(image_url, saved_file_path)
            if is_save_success:
                saved_file_path_list.append(saved_file_path)

            print(f'{name}\'s icon saved')

        dprint('Download finish, {num} files saved'.format(num=len(saved_file_path_list)))
        return saved_file_path_list
        
