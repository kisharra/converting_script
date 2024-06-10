import sqlite3
import subprocess
import json
import os
from datetime import datetime
import logging
import signal
import sys
from get_info import run_ffprobe
from get_info import streams_data



class ConvertTask:
    '''Class for converting videos to mp4 format'''
    def __init__(self, config):
        '''initialize class variables'''
        self.config = config
        self.bitrate_video_film = config['bitrate_video_film']
        self.bitrate_video_serials = config['bitrate_video_serial']
        self.b_a = config['bitrate_audio']
        self.interrupted = False
        self.remove_list = []
        self.file_id = None
        logging.basicConfig(filename=config['log_file'], level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s') #logging to file

    
    def signal_handler(self, signum, frame):
        '''Signal handler for SIGINT signal'''
        logging.error('Program interrupted manually')
        self.interrupted = True
        for file in self.remove_list:  #remove temporary files
            os.remove(file)
        if self.file_id is not None:
            conn = sqlite3.connect(self.config['db_file'])
            c = conn.cursor()
            try:
                current_time = datetime.now().strftime(config['data_format'])
                c.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE file_id=?', ('Program interrupted manually', current_time, self.file_id))  #update database
                conn.commit()
            except Exception as e:
                logging.error(f'Error updating database: {e}')
            finally:
                conn.close()
        sys.exit(1)


    def run_ffmpeg(self, input_file, output_file, bitrate):
        '''run ffmpeg command'''
        command = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=self.b_a) for arg in self.config['ffmpeg_command']]  #run ffmpeg command which is in config
        subprocess.run(command, check=True)


    def check_integrity(self, output_file):
        '''check if output file is corrupted'''
        command = [arg.format(output_file=output_file) for arg in self.config['ffmpeg_check_command']]  #run ffmpeg check command which is in config
        process = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
        _, stderr_data = process.communicate()
        if process.returncode != 0:
            return False, stderr_data.decode('utf-8')
        else:
            return True, 'No errors found'


    def convert_files(self, db_file):
        '''convert files to mp4 format'''
        signal.signal(signal.SIGINT, self.signal_handler)  #register signal handler
        
        conn = sqlite3.connect(db_file)  #connect to database
        c = conn.cursor()

        c.execute('SELECT id, IsFilm, IsSerial, filename, nb_streams, streams FROM Files')  #select data from database
        video_files = c.fetchall()

        for file_id, IsFilm, IsSerial, filename, nb_streams, streams in video_files:  #iterate through files
            self.file_id = file_id
            if self.interrupted:
                break
                
            if nb_streams > 2:  #check if file contains more than 2 streams
                streams_info = json.loads(streams)
                video_streams = [stream for stream in streams_info if stream['codec_type'] == 'video' and stream['index'] == 0]
                audio_streams = [stream for stream in streams_info if stream['codec_type'] == 'audio' and 'rus' in stream.get('tags', {}).get('language', '') and stream['codec_name'] == 'ac3' and stream['disposition'].get('default', 0) == 1 or stream['index'] == 1]

                if len(video_streams) > 0 and len(audio_streams) > 0:  #check if file contains video and audio streams
                    output_file = os.path.splitext(filename)[0] + '.mp4'  #create output file
                    self.remove_list.append(output_file)  #add file to remove list
                        
                    current_time = datetime.now().strftime(config['data_format'])  #set datetime of starting conversion
                    c.execute('INSERT INTO ConversionTasks (file_id, status, start_time) VALUES (?, ?, ?)', (file_id, 'converting', current_time))  #update status of conversion
                    conn.commit()  

                    try:
                        if IsFilm == True:  #check if file is a film
                            bitrate = self.bitrate_video_film  #set bitrate
                        else:
                            bitrate = self.bitrate_video_serials
                        self.run_ffmpeg(filename, output_file, bitrate)  #run ffmpeg

                        current_time = datetime.now().strftime(config['data_format'])  #set datetime of ending conversion
                        success, check_result = self.check_integrity(output_file)  #check if output file is corrupted
                        if success:
                            c.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', ('done', current_time, check_result, file_id))  #update status of conversion
                            video_info = run_ffprobe(output_file, config)  #get video info of converted file
                            if video_info:
                                streams = streams_data(video_info)  #get streams info of converted file
                                c.execute('UPDATE Files SET filename=?, IsConverted=?, nb_streams=?, streams=? WHERE id=?', (output_file, True, len(streams), json.dumps(streams), file_id))  #update table 'Files' with new data
                            conn.commit()
                            # os.remove(filename)  #remove original file
                        else:
                            c.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', (check_result, current_time, check_result, file_id))  #update status of checking
                            conn.commit()

                            # os.remove(output_file)

                    except Exception as e:  #catch errors
                        current_time = datetime.now().strftime(config['data_format'])
                        error_messege = str(e)
                        logging.error(f'{filename}: {error_messege}')
                        c.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE file_id=?', (error_messege, current_time, file_id))  #write error to database
                        conn.commit()
                        # os.remove(output_file)  #remove temporary file

        conn.close()


if __name__ == '__main__':
    with open ('config.json', 'r') as config_file:  #read config file
        config = json.load(config_file)

    start_convert = ConvertTask(config)  #initialize class
    start_convert.convert_files(config['db_file'])  #start conversion
