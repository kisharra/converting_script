from datetime import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile

from conversion.get_info import Get_Info
from db_query.db_query import Db_query
from custom_logging.logger import CustomLogger

custom_logger = CustomLogger(log_dir="logs", max_files=30, rotation_interval=30)
logger = custom_logger.get_logger()



class ConvertTask:
    '''Class for converting videos to mp4 format'''
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
        maria_db : dict
            config of maria database
        data_format : str
            format of date and time
        ffmpeg_cpu : list of str
            list of arguments for ffmpeg command with cpu
        ffmpeg_nvidia : list of str
            list of arguments for ffmpeg command with nvidia driver
        ffmpeg_check_command : list of str
            list of arguments for ffmpeg command to check integrity of output file
        bitrate_video_film : str
            bitrate of video streams of film
        bitrate_video_serials : str
            bitrate of video streams of serials
        b_a : str
            bitrate of audio streams
        interrupted : bool
            flag to check if program is interrupted
        remove_list : list
            list of files to remove
        file_id : int
            id of current file
        get_info : Get_Info
            instance of Get_Info class
        db_file : Db_query
            instance of Db_query class
        """
        self.config = config
        self.db_file = os.path.join(config['path_to_main'], config['sqlite3'])
        self.maria_db = config['maria_db']
        self.data_format = config['data_format']
        self.ffmpeg_cpu = config['ffmpeg_cpu']
        self.ffmpeg_when_error = config['ffmpeg_when_error']
        self.ffmpeg_check_command = config['ffmpeg_check_command']
        self.bitrate_video_film = config['bitrate_video_film']
        self.bitrate_video_serials = config['bitrate_video_serial']
        self.b_a = config['bitrate_audio']
        self.tmp_dir = os.path.join(config['path_to_main'], config['temp_dir'])
        self.interrupted = False
        self.file_id = None
        self.get_info = Get_Info(config)
        self.db_file = Db_query(config)
    
    def signal_handler(self, signum, frame):
        '''
        Signal handler for SIGINT signal
        '''
        logger.error('Program interrupted manually')
        self.interrupted = True
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        os.mkdir(self.tmp_dir)
        if self.file_id is not None:
            self.db_file.interrupted_program(datetime.now().strftime(self.data_format), self.file_id)
        sys.exit(1)

    def run_ffmpeg(self, input_file, output_file, bitrate, audio_stream_index):
        '''
        Run ffmpeg command

        Parameters
        ----------
        input_file : str
            path to input file
        output_file : str
            path to output file
        bitrate : str
            bitrate of video stream

        Returns
        -------
        bool
            result of conversion
        '''
        try:
            command = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=self.b_a, audio_stream_index=audio_stream_index) for arg in self.ffmpeg_cpu]  #run ffmpeg command with cpu which is in config
            subprocess.run(command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running ffmpeg: {e}")
            return False
    
    def run_ffmpeg_when_error(self, input_file, output_file, bitrate):
        try:
            command = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=self.b_a) for arg in self.ffmpeg_when_error]  #run ffmpeg command with cpu which is in config
            subprocess.run(command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running ffmpeg: {e}")
            return False

    def check_integrity(self, output_file):
        '''
        Check if output file is corrupted

        Parameters
        ----------
        output_file : str
            path to output file

        Returns
        -------
        tuple
            (bool, str) where bool is result of check and str is error or 'No errors found'
        '''
        # Inform about check
        print(f"Checking file {output_file} if corrupted...")
        try:
            result = subprocess.run([arg.format(output_file=output_file) for arg in self.ffmpeg_check_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                return False, result.stderr
            else:
                return True, 'No errors found'
        except Exception as e:
            return False, str(e)
        
    def convert_files(self, file_data):
        '''
        Convert files to mp4 format

        This function iterate through files in 'Files' table in database,
        check if file contains more than 2 streams, run ffmpeg command to convert
        file to mp4 format, check if output file is corrupted and if not, move
        it to original location, update 'Files' table with new data and remove
        original file.

        If an error occurs during conversion, log it and update status of
        checking integrity in 'ConversionTasks' table.

        If conversion is interrupted manually, remove temporary files and update
        status of conversion in 'ConversionTasks' table.
        '''
        signal.signal(signal.SIGINT, self.signal_handler)  # register signal handler

        video_files = self.db_file.select_single_data(file_data)

        for file_id, IsFilm, IsConverted, filename, nb_streams, streams in video_files:  # iterate through files
            self.file_id = file_id
            if self.interrupted:
                break

            if nb_streams > 2:  # check if file contains more than 2 streams
                streams_info = json.loads(streams)

                default_rus_index = None
                first_rus_index = None

                # iterate through streams and find default=1 track
                for stream in streams_info:
                    if stream['codec_type'] == 'audio':
                        language = stream.get('tags', {}).get('language', '')
                        is_default = stream.get('disposition', {}).get('default', 0)

                        if language == 'rus':
                            if is_default == 1:
                                default_rus_index = stream['index']
                            if first_rus_index is None:
                                first_rus_index = stream['index']

                # Priority - track with default=1, if default=1 not found
                if default_rus_index is not None:
                    selected_index = default_rus_index
                elif first_rus_index is not None:
                    selected_index = first_rus_index
                else:
                    selected_index = None
                
                # Check if file is corrupted before conversion
                success, check_result = self.check_integrity(filename)
                
                if not success:  # if file is corrupted
                    self.db_file.update_status_first_check(file_id, 'Error: check logs', datetime.now().strftime(self.data_format), datetime.now().strftime(self.data_format))
                    self.db_file.update_isconverted_after_fail_check(file_id, True)
                    logger.error(f'{filename} is corrupted. Upload a new working file to ftp.sat-dv.ru')
                    continue  # Skip this file

                if not IsConverted:
                    os.makedirs(self.tmp_dir, exist_ok=True)  # Create temporary directory

                    with tempfile.TemporaryDirectory(dir=self.tmp_dir) as temp_dir:
                        
                        output_file = os.path.join(temp_dir, os.path.splitext(os.path.basename(filename))[0] + '.mp4')  # Create output file path in temp directory
                        self.db_file.update_status_of_conversion(file_id, 'converting', datetime.now().strftime(self.data_format))

                        try:
                            if IsFilm:  # Check if file is a film
                                bitrate = self.bitrate_video_film  # Set bitrate
                            else:
                                bitrate = self.bitrate_video_serials
                            if selected_index is not None:    
                                success = self.run_ffmpeg(filename, output_file, bitrate, selected_index)  #run ffmpeg
                            else:
                                success = self.run_ffmpeg_when_error(filename, output_file, bitrate)
            
                            if success:
                                success, check_result = self.check_integrity(output_file)  # Check if output file is corrupted
                                if success:
                                    final_path = os.path.join(os.path.dirname(filename), os.path.basename(output_file))  # Path to move final file
                                    shutil.move(output_file, final_path)  # Move file to original location
                                    self.db_file.update_status_ending_conversion('done', datetime.now().strftime(self.data_format), check_result, file_id)
                                    video_info = self.get_info.run_ffprobe(final_path)  # Get video info of converted file
                                    logger.info(f'{filename} converted, new url: {final_path}')  # Log success
                                    if video_info:
                                        streams = self.get_info.streams_data(video_info)  # Get streams info of converted file
                                        self.db_file.update_files_table(final_path, True, len(streams), video_info['format']['size'], video_info['format']['bit_rate'], json.dumps(streams), file_id)  # Update table 'Files' with new data
                                        self.db_file.update_url_file(filename, final_path)  # Update table 'Video_Series_Files' on Stalker Portal with new url
                                    if os.path.exists(final_path) and os.path.exists(filename):    
                                        os.remove(filename) # remove original file
                                        logger.info(f'{filename} removed')
                                    else:
                                        logger.error(f'{final_path} unavailable after conversion.')
                                        self.db_file.update_of_checking_integrity('Error', datetime.now().strftime(self.data_format), 'Error: check logs', file_id)  #update status of checking
                                        self.db_file.update_isconverted_after_fail_check(file_id, True)
                                else:
                                    logger.error(f'{filename} is corrupted after conversion.')  # Log error
                                    self.db_file.update_of_checking_integrity('Error', datetime.now().strftime(self.data_format), 'Error: check logs', file_id)  # Update status of checking
                                    self.db_file.update_isconverted_after_fail_check(file_id, True)

                        except Exception as e:  # Catch errors
                            error_message = str(e)
                            logger.error(f'{filename}: {error_message}')  # Log errors


# if __name__ == '__main__':
#     pass
