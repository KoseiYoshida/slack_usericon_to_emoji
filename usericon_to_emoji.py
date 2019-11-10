import os

from dotenv import load_dotenv


from icon_download import Downloader
from icon_upload import Uploader


SAVE_DIRECTORY_NAME = 'saved_icons'

def add_env_variables():

	dotenv_path = os.path.join(os.path.curdir, '.env')
	load_dotenv(dotenv_path, override=True)

def main():

	add_env_variables()
	token = os.getenv('SLACK_API_TOKEN')
	team_name = os.getenv('SLACK_TEAM')
	cookie = os.getenv('SLACK_COOKIE')


	icon_downloader = Downloader(token)
	saved_file_path_list = icon_downloader.download(SAVE_DIRECTORY_NAME)
	
	if len(saved_file_path_list) < 1:
		('No file was saved, stop upload')
		return

	icon_uploader = Uploader(team_name=team_name, token=token, cookie=cookie)
	icon_uploader.upload(saved_file_path_list)

	

if __name__ == "__main__":
    
	main()
