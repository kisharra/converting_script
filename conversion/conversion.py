import subprocess
import json
import os
from datetime import datetime
import logging
import signal
import sys
from conversion.db_querry import Db_querry



class Get_Info:
    def __init__(self, config):
        self.config = config
        self.db_file = config['db_file']
        self.ffprobe_command = config['ffprobe_command']
        self.log_file = config['log_file']
        logging.basicConfig(filename=self.log_file, level=logging.ERROR, format='%(asctime)s:%(message)s')  #logging to file
        self.db_querry = Db_querry(config)

    def get_video_info(self, directory):
        '''get video info in directory'''
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
        '''run ffprobe command'''
        command = [arg.format(file_path=file_path) for arg in self.ffprobe_command]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logging.error(f"Error running ffprobe for {file_path}: {result.stderr}")
            return 

    def streams_data(self, data):
        '''transform streams data to get only audio and video streams'''
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

class ConvertTask:
    '''Class for converting videos to mp4 format'''
    def __init__(self, config):
        '''initialize class variables'''
        self.config = config
        self.db_file = config['db_file']
        self.maria_db = config['maria_db']
        self.log_file = config['log_file']
        self.data_format = config['data_format']
        self.ffmpeg_cpu = config['ffmpeg']
        self.ffmpeg_check_command = config['ffmpeg_check_command']
        self.bitrate_video_film = config['bitrate_video_film']
        self.bitrate_video_serials = config['bitrate_video_serial']
        self.b_a = config['bitrate_audio']
        self.interrupted = False
        self.remove_list = []
        self.file_id = None
        self.get_info = Get_Info(config)
        self.db_file = Db_querry(config)
        logging.basicConfig(filename=self.log_file, level=logging.ERROR, format='%(asctime)s:%(message)s')  #logging to file
    
    def signal_handler(self, signum, frame):
        '''Signal handler for SIGINT signal'''
        logging.error('Program interrupted manually')
        self.interrupted = True
        for file in self.remove_list:  #remove temporary files
            os.remove(file)
        if self.file_id is not None:
            self.db_file.interrupted_program(datetime.now().strftime(self.data_format), self.file_id)
        sys.exit(1)

    def run_ffmpeg(self, input_file, output_file, bitrate):
        '''run ffmpeg command'''
        if self.check_nvidia_driver():
            try:
                command = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=self.b_a) for arg in self.ffmpeg_nvidia]  #run ffmpeg command which is in config
                subprocess.run(command, check=True)
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running ffmpeg: {e}")
                return False
        else:
            try:
                command = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=self.b_a) for arg in self.ffmpeg_cpu]  #run ffmpeg command which is in config
                subprocess.run(command, check=True)
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running ffmpeg: {e}")
                return False

    def check_integrity(self, output_file):
        '''check if output file is corrupted'''
        try:
            result = subprocess.run([arg.format(output_file=output_file) for arg in self.ffmpeg_check_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                return False, result.stderr.decode('utf-8')
            else:
                return True, 'No errors found'
        except Exception as e:
            return False, str(e)

    def convert_files(self):
        '''convert files to mp4 format'''
        signal.signal(signal.SIGINT, self.signal_handler)  #register signal handler

        video_files = self.db_file.select_data()

        for file_id, IsFilm, IsConverted, filename, nb_streams, streams in video_files:  #iterate through files
            self.file_id = file_id
            if self.interrupted:
                break
                
            if nb_streams > 2:  #check if file contains more than 2 streams
                streams_info = json.loads(streams)
                video_streams = [stream for stream in streams_info if stream['codec_type'] == 'video' and stream['index'] == 0]
                audio_streams = [stream for stream in streams_info if stream['codec_type'] == 'audio' and 'rus' in stream.get('tags', {}).get('language', '') and stream['codec_name'] == 'ac3' and stream['disposition'].get('default', 0) == 1 or stream['index'] == 1]
                
                if not IsConverted:

                    if len(video_streams) > 0 and len(audio_streams) > 0:  #check if file contains video and audio streams
                        output_file = os.path.splitext(filename)[0] + '.mp4'  #create output file
                        self.remove_list.append(output_file)  #add file to remove list
                            
                        self.db_file.update_status_of_conversion(file_id, 'converting', datetime.now().strftime(self.data_format))

                        try:
                            if IsFilm:  #check if file is a film
                                bitrate = self.bitrate_video_film  #set bitrate
                            else:
                                bitrate = self.bitrate_video_serials
                            self.run_ffmpeg(filename, output_file, bitrate)  #run ffmpeg
                    
                            success, check_result = self.check_integrity(output_file)  #check if output file is corrupted
                            if success:
                                self.db_file.update_status_ending_conversion('done', datetime.now().strftime(self.data_format), check_result, file_id)
                                video_info = self.get_info.run_ffprobe(output_file)  #get video info of converted file
                                if video_info:
                                    streams = self.get_info.streams_data(video_info)  #get streams info of converted file
                                    self.db_file.update_files_table(output_file, True, len(streams), video_info['format']['size'], video_info['format']['bit_rate'], json.dumps(streams), file_id)  #update table 'Files' with new data
                                    self.db_file.update_url_file(filename, output_file)  #update table 'Video_Series_Files' on Stalker Portal with new url
                                # os.remove(filename)  #remove original file
                            else:
                                logging.error(f'{filename}: {check_result}')
                                self.db_file. update_of_checking_integrity('Error', datetime.now().strftime(self.data_format), 'Error: check logs', file_id)  #update status of checking

                                # os.remove(output_file)

                        except Exception as e:  #catch errors
                            error_messege = str(e)
                            logging.error(f'{filename}: {error_messege}')  #logging errors

                            # os.remove(output_file)  #remove temporary file

if __name__ == '__main__':
    pass