import json
import logging
import os
import subprocess

from conversion.db_querry import Db_querry


class Get_Info:
    def __init__(self, config):
        self.config = config
        self.db_file = config['db_file']
        self.ffprobe_command = config['ffprobe_command']
        self.log_file = config['log_file']
        logging.basicConfig(filename=self.log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')  # updated logging level
        self.db_querry = Db_querry(config)

    def get_video_info(self, directory):
        video_files = []
        subdirectories = []
        for root, dirs, files in os.walk(directory):
            if root[-2:] in ("/A", "/0", "/1", "/2", "/3", "/4", "/5", "/6", "/7", "/8", "/9",
                            "/B", "/C", "/D", "/E", "/F", "/G", "/H", "/I", "/J", "/K",
                            "/L", "/M", "/N", "/O", "/P", "/Q", "/R", "/S", "/T", "/U",
                            "/V", "/W", "/X", "/Y", "/Z", "/temp"):
                for file in files:
                    file_path = os.path.join(root, file)
                    video_files.append(file_path)
                    video_info = self.run_ffprobe(file_path)
                    if video_info:
                        streams = self.streams_data(video_info)
                        self.db_querry.save_file_data(video_info, streams, is_film=True, is_serial=False)
                    else:
                        logging.warning(f"No video info for file: {file_path}")
                                
                for subdir in dirs:
                    subdir_path = os.path.join(root, subdir)
                    if os.path.isdir(subdir_path):
                        for sub_root, sub_dirs, sub_files in os.walk(subdir_path):
                            for sub_file in sub_files:
                                sub_file_path = os.path.join(sub_root, sub_file)
                                video_info = self.run_ffprobe(sub_file_path)
                                if video_info:
                                    streams = self.streams_data(video_info)
                                    self.db_querry.save_file_data(video_info, streams, is_film=False, is_serial=True)
                                else:
                                    logging.warning(f"No video info for file: {sub_file_path}")

        return video_files, subdirectories

    def run_ffprobe(self, file_path):
        command = [arg.format(file_path=file_path) for arg in self.ffprobe_command]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON for {file_path}: {result.stdout}")
                return None
        else:
            logging.error(f"Error running ffprobe for {file_path}: {result.stderr}")
            return None

    def streams_data(self, data):
        transformed_streams = []
        for stream in data.get('streams', []):
            transformed_stream = {
                'index': stream['index'],
                'codec_name': stream['codec_name'],
                'codec_long_name': stream['codec_long_name'],
                'codec_type': stream['codec_type'],
                'disposition': {
                    'default': stream['disposition']['default']
                }
            }
            if 'tags' in stream:
                transformed_stream['tags'] = {
                    'language': stream['tags'].get('language'),
                    'title': stream['tags'].get('title')
                }
            transformed_streams.append(transformed_stream)
        
        return transformed_streams
    
if __name__ == '__main__':
    pass