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
        ffprobe_command : list of str
            list of arguments for ffprobe command
        log_file : str
            path to log file
        db_querry : Db_querry
            instance of Db_querry class
        """
        self.config = config
        self.db_file = config['db_file']
        self.ffprobe_command = config['ffprobe_command']
        self.log_file = config['log_file']
        logging.basicConfig(filename=self.log_file, level=logging.ERROR, format='%(asctime)s:%(message)s')  #logging to file
        self.db_querry = Db_querry(config)

    def get_video_info(self, directory):
        """
        Get video info in directory

        Parameters
        ----------
        directory : str
            path to directory

        Returns
        -------
        video_files : list
            list of video files
        subdirectories : list
            list of subdirectories
        """

        video_files = []
        subdirectories = []
        for root, dirs, files in os.walk(directory):  #iterate through directory
            if root[-2:] in ("/A", "/0", "/1", "/2", "/3", "/4", "/5", "/6", "/7", "/8", "/9",
                            "/B", "/C", "/D", "/E", "/F", "/G", "/H", "/I", "/J", "/K",
                            "/L", "/M", "/N", "/O", "/P", "/Q", "/R", "/S", "/T", "/U",
                            "/V", "/W", "/X", "/Y", "/Z"):
                for file in files:  #iterate through files
                    file_path = os.path.join(root, file)  #create file path
                    video_files.append(file_path)  #add file to list
                    video_info = self.run_ffprobe(file_path)  #run ffprobe command
                    if video_info:  #check if video info is not empty
                        streams = self.streams_data(video_info)  #transform streams data
                        self.db_querry.save_films(video_info, streams)  #save data to database
                                
                for subdir in dirs:  #iterate through subdirectories
                    subdir_path = os.path.join(root, subdir)
                    if os.path.isdir(subdir_path):
                        for sub_root, sub_dirs, sub_files in os.walk(subdir_path):
                            for sub_file in sub_files:
                                sub_file_path = os.path.join(sub_root, sub_file)
                                video_info = self.run_ffprobe(sub_file_path)
                                if video_info:
                                    streams = self.streams_data(video_info)
                                    self.db_querry.save_serials(video_info, streams)

        return video_files, subdirectories


    def run_ffprobe(self, file_path):
        '''
        Run ffprobe command

        Parameters
        ----------
        file_path : str
            path to file

        Returns
        -------
        video_info : dict
            video info or None if an error occurs
        '''

        command = [arg.format(file_path=file_path) for arg in self.ffprobe_command]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logging.error(f"Error running ffprobe for {file_path}: {result.stderr}")
            return 

    def streams_data(self, data):
        '''
        Transform streams data to get only audio and video streams

        Parameters
        ----------
        data : dict
            video info

        Returns
        -------
        transformed_streams : list
            list of transformed streams
        '''
        transformed_streams = []
        for stream in data['streams']:  
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