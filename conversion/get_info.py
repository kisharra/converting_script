import json
import os
import subprocess

from db_query.db_query import Db_query
from custom_logging.logger import CustomLogger

custom_logger = CustomLogger(log_dir="logs", max_files=30, rotation_interval=30)
logger = custom_logger.get_logger()

class Get_Info:
    def __init__(self, config):
        """
        Initialize class variables

        Parameters
        ----------
        config : dict
            config dictionary

        Attributes
        ----------
        config : dict
            config dictionary
        db_file : str
            path to database file
        ffprobe_command : str
            command to run ffprobe
        Db_query : Db_query
            instance of Db_query class
        """
        self.config = config
        self.db_file = os.path.join(config['path_to_main'], config['sqlite3'])
        self.ffprobe_command = config['ffprobe_command']
        self.Db_query = Db_query(config)

    def get_all_files_info(self, directory):
        """
        Get all files info in directory and subdirectories

        Parameters
        ----------
        directory : str
            path to directory

        Returns
        -------
        video_files : list of str
            list of files
        subdirectories : list of str
            list of subdirectories
        """
        
        video_files = []
        subdirectories = []
        for root, dirs, files in os.walk(directory):
            if os.path.dirname(root) == directory:
                for file in files:
                    file_path = os.path.join(root, file)
                    video_files.append(file_path)
                    video_info = self.run_ffprobe(file_path)
                    if video_info:
                        streams = self.streams_data(video_info)
                        self.Db_query.save_file_data(video_info, streams, is_film=True, is_serial=False)
                    else:
                        logger.warning(f"No video info for file: {file_path}")
                                
                for subdir in dirs:
                    subdir_path = os.path.join(root, subdir)
                    if os.path.isdir(subdir_path):
                        for sub_root, sub_dirs, sub_files in os.walk(subdir_path):
                            for sub_file in sub_files:
                                sub_file_path = os.path.join(sub_root, sub_file)
                                video_info = self.run_ffprobe(sub_file_path)
                                if video_info:
                                    streams = self.streams_data(video_info)
                                    self.Db_query.save_file_data(video_info, streams, is_film=False, is_serial=True)
                                else:
                                    logger.warning(f"No video info for file: {sub_file_path}")

        return video_files, subdirectories
    
    def get_single_file_info(self, file_path, is_film, is_serial):
        """
        Get video info for a single file and save it to database.

        Parameters
        ----------
        file_path : str
            path to file
        is_film : bool
            flag indicating if the file is a film
        is_serial : bool
            flag indicating if the file is a serial
        """
        video_info = self.run_ffprobe(file_path)
        if video_info:
            streams = self.streams_data(video_info)
            self.Db_query.save_file_data(video_info, streams, is_film, is_serial)
        else:
            logger.warning(f"No video info for file: {file_path}")

    def get_directory_info(self, directory, is_film, is_serial):
        """
        Get video info for all files in directory and subdirectories.

        Parameters
        ----------
        directory : str
            path to directory
        is_film : bool
            flag indicating if the files is a film
        is_serial : bool
            flag indicating if the files is a serial
        """
        
        video_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                video_files.append(file_path)
                video_info = self.run_ffprobe(file_path)
                if video_info:
                    streams = self.streams_data(video_info)
                    self.Db_query.save_file_data(video_info, streams, is_film=is_film, is_serial=is_serial)
                else:
                    logger.warning(f"No video info for file: {file_path}")

        return video_files
                                
    def run_ffprobe(self, file_path):
        """
        Run ffprobe command on given file and return its output as a dict.

        Parameters
        ----------
        file_path : str
            path to file

        Returns
        -------
        dict or None
            json output of ffprobe command or None if an error occurs
        """
        command = [arg.format(file_path=file_path) for arg in self.ffprobe_command]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"ERROR - decoding JSON failed with file {file_path}: {result.stdout}")
                return None
        elif not json.loads(result.stdout):
            logger.error(f"ERROR - ffprobe failed with file {file_path}: Empty output")
        else:
            logger.error(f"ERROR - ffprobe failed with file {file_path}: {result.stderr}")
            print(result.stderr)
            return None

    def streams_data(self, data):
        """
        Transform a list of streams from ffprobe output into a simplified list of dicts.

        Parameters
        ----------
        data : dict
            output of ffprobe command

        Returns
        -------
        list of dict
            list of streams with simplified keys
        """
        transformed_streams = []
        for stream in data.get('streams', []):
            transformed_stream = {
                'index': stream['index'],
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
    
# if __name__ == '__main__':
#     pass