import sqlite3
import subprocess
import json
import os
from datetime import datetime
import logging
import signal
import sys



class Get_Info:
    def __init__(self, config):
        self.config = config
        self.db_file = config['db_file']
        self.ffprobe_command = config['ffprobe_command']
        self.directory_path = config['file_path']
        self.log_file = config['log_file']
        logging.basicConfig(filename=self.log_file, level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')  #logging to file

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
                        try:
                            self.save_films(video_info, streams)  #save data to database
                        except sqlite3.Error as e:
                            print(f"Error saving data: {e}")
                                
                for subdir in dirs:  #iterate through subdirectories
                    subdir_path = os.path.join(root, subdir)
                    if os.path.isdir(subdir_path):
                        for sub_root, sub_dirs, sub_files in os.walk(subdir_path):
                            for sub_file in sub_files:
                                sub_file_path = os.path.join(sub_root, sub_file)
                                video_info = self.run_ffprobe(sub_file_path)
                                if video_info:
                                    streams = self.streams_data(video_info)
                                    try:
                                        self.save_serials(video_info, streams)
                                    except sqlite3.Error as e:
                                        print(f"Error saving data: {e}")
        return video_files, subdirectories


    def run_ffprobe(self, file_path):
        '''run ffprobe command'''
        command = [arg.format(file_path=file_path) for arg in self.ffprobe_command]
        logging.debug(f"Running ffprobe command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.debug(f"ffprobe output: {result.stdout}")
            return json.loads(result.stdout)
        elif file_path is None:
            logging.error("Conversion did not produce a valid output path.")
            return
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


    def save_films(self, data, streams):
        '''save film data to database'''
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Files WHERE filename = ?', (data['format']['filename'],))  #check if data already exists
            count = cur.fetchone()
            if count is None:
                cur.execute("""INSERT INTO Files (filename, IsFilm, IsSerial, IsConverted, nb_streams, size, bit_rate, streams)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (data['format']['filename'],True, False, False, data['format']['nb_streams'], 
                            data['format']['size'], data['format']['bit_rate'], json.dumps(streams)))
                conn.commit()
            else:
                print(f"Data already exists for {data['format']['filename']}")

    def save_serials(self, data, streams):
        '''save serials data to database'''
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Files WHERE filename = ?', (data['format']['filename'],))  #check if data already exists
            count = cur.fetchone()
            if count is None:
                cur.execute("""INSERT INTO Files (filename, IsFilm, IsSerial, IsConverted, nb_streams, size, bit_rate, streams) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                            (data['format']['filename'], False, True, False, data['format']['nb_streams'], 
                            data['format']['size'], data['format']['bit_rate'], json.dumps(streams)))
                conn.commit()
            else:
                print(f"Data already exists for {data['format']['filename']}")


class ConvertTask:
    '''Class for converting videos to mp4 format'''
    def __init__(self, config):
        '''initialize class variables'''
        self.config = config
        self.db_file = config['db_file']
        self.log_file = config['log_file']
        self.data_format = config['data_format']
        self.ffmpeg_command = config['ffmpeg_command']
        self.ffmpeg_check_command = config['ffmpeg_check_command']
        self.file_path = config['file_path']
        self.bitrate_video_film = config['bitrate_video_film']
        self.bitrate_video_serials = config['bitrate_video_serial']
        self.b_a = config['bitrate_audio']
        self.interrupted = False
        self.remove_list = []
        self.file_id = None
        self.get_info = Get_Info(config)
        logging.basicConfig(filename=self.log_file, level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')  #logging to file

    
    def signal_handler(self, signum, frame):
        '''Signal handler for SIGINT signal'''
        logging.error('Program interrupted manually')
        self.interrupted = True
        for file in self.remove_list:  #remove temporary files
            os.remove(file)
        if self.file_id is not None:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            try:
                current_time = datetime.now().strftime(self.data_format)
                c.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE file_id=?', ('Program interrupted manually', current_time, self.file_id))  #update database
                conn.commit()
            except Exception as e:
                logging.error(f'Error updating database: {e}')  #logging errors 
            finally:
                conn.close()
        sys.exit(1)


    def run_ffmpeg(self, input_file, output_file, bitrate):
        '''run ffmpeg command'''
        command = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=self.b_a) for arg in self.ffmpeg_command]  #run ffmpeg command which is in config
        subprocess.run(command, check=True)

    def check_integrity(self, output_file):
        '''check if output file is corrupted'''
        command = [arg.format(output_file=output_file) for arg in self.ffmpeg_check_command]  #run ffmpeg check command which is in config
        process = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
        _, stderr_data = process.communicate()
        if process.returncode != 0:
            return False, stderr_data.decode('utf-8')
        else:
            return True, 'No errors found'


    def convert_files(self):
        '''convert files to mp4 format'''
        signal.signal(signal.SIGINT, self.signal_handler)  #register signal handler
        
        conn = sqlite3.connect(self.db_file)  #connect to database
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
                        
                    current_time = datetime.now().strftime(self.data_format)  #set datetime of starting conversion
                    c.execute('INSERT INTO ConversionTasks (file_id, status, start_time) VALUES (?, ?, ?)', (file_id, 'converting', current_time))  #update status of conversion
                    conn.commit()  

                    try:
                        if IsFilm == True:  #check if file is a film
                            bitrate = self.bitrate_video_film  #set bitrate
                        else:
                            bitrate = self.bitrate_video_serials
                        self.run_ffmpeg(filename, output_file, bitrate)  #run ffmpeg
                
                        current_time = datetime.now().strftime(self.data_format)  #set datetime of ending conversion
                        success, check_result = self.check_integrity(output_file)  #check if output file is corrupted
                        if success:
                            c.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', ('done', current_time, check_result, file_id))  #update status of conversion
                            video_info = self.get_info.run_ffprobe(output_file)  #get video info of converted file
                            if video_info:
                                streams = self.get_info.streams_data(video_info)  #get streams info of converted file
                                c.execute('UPDATE Files SET filename=?, IsConverted=?, nb_streams=?, streams=? WHERE id=?', (output_file, True, len(streams), json.dumps(streams), file_id))  #update table 'Files' with new data
                            conn.commit()
                            # os.remove(filename)  #remove original file
                        else:
                            c.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', (check_result, current_time, check_result, file_id))  #update status of checking
                            conn.commit()

                            # os.remove(output_file)

                    except Exception as e:  #catch errors
                        current_time = datetime.now().strftime(self.data_format)
                        error_messege = str(e)
                        logging.error(f'{filename}: {error_messege}')  #logging errors
                        c.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE file_id=?', (error_messege, current_time, file_id))  #write error to database
                        conn.commit()
                        # os.remove(output_file)  #remove temporary file

        conn.close()


if __name__ == '__main__':
    pass