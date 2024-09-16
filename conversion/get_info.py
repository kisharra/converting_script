import json
import logging
import os
import subprocess

from conversion.db_querry import Db_querry


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
        log_file : str
            path to log file
        db_querry : Db_querry
            instance of Db_querry class
        """
        self.config = config
        self.db_file = os.path.join(config['path_to_main'], config['sqlite3'])
        self.ffprobe_command = config['ffprobe_command']
        self.log_file = os.path.join(config['path_to_main'], config['log_file'])
        logging.basicConfig(filename=self.log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')  # updated logging level
        self.db_querry = Db_querry(config)

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
            self.db_querry.save_file_data(video_info, streams, is_film, is_serial)
        else:
            logging.warning(f"No video info for file: {file_path}")

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
                logging.error(f"Error decoding JSON for {file_path}: {result.stdout}")
                return None
        else:
            logging.error(f"Error running ffprobe for {file_path}: {result.stderr}")
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