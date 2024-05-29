import sqlite3
import subprocess
import json
import os
from datetime import datetime
import logging
import signal
import sys



__data_format__='%Y-%m-%d %H:%M:%S'

logging.basicConfig(filename='/file_storage/work_scripts/logs/convert_logs.log', level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')

class ConvertTask:
    def __init__(self, b_v, b_a):
        self.b_v = b_v
        self.b_a = b_a
        self.interrupted = False
        self.remove_list = []
        self.films_id = None

    
    def signal_handler(self, signum, frame):
        logging.error('Program interrupted manually')
        self.interrupted = True
        for file in self.remove_list:
            os.remove(file)
        if self.films_id is not None:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            try:
                current_time = datetime.now().strftime(__data_format__)
                c.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE films_id=?', ('Program interrupted manually', current_time, self.films_id))
                conn.commit()
            except Exception as e:
                logging.error(f'Error updating database: {e}')
            finally:
                conn.close()
        sys.exit(1)


    def run_ffmpeg(self, input_file, output_file):

        command = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264',
            '-c:a', 'ac3',
            '-map', '0:v:0',
            '-map', '0:a:0',
            '-b:v', self.b_v,
            '-b:a', self.b_a,
            '-preset:v', 'ultrafast',
            '-strict', 'experimental',
            '-movflags', '+faststart',
            output_file
        ]
        subprocess.run(command, check=True)


    def check_integrity(self, output_file):
        command = ['ffmpeg', '-v', 'error', '-i', output_file, '-f', 'null', '-']
        process = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
        error = process.communicate()
        if process.returncode != 0:
            return False, error.decode('utf-8')
        else:
            return True, 'No errors found'


    def convert_films(self, db_file):
        signal.signal(signal.SIGINT, self.signal_handler)
        
        conn = sqlite3.connect(db_file)
        c = conn.cursor()

        c.execute('SELECT id, filename, nb_streams, streams FROM Films')
        video_files = c.fetchall()

        for films_id, filename, nb_streams, streams in video_files:
            self.films_id = films_id
            if self.interrupted:
                break
                
            if nb_streams > 2:
                streams_info = json.loads(streams)
                video_streams = [stream for stream in streams_info if stream['codec_type'] == 'video' and stream['index'] == 0]
                audio_streams = [stream for stream in streams_info if stream['codec_type'] == 'audio' and 'rus' in stream.get('tags', {}).get('language', '') and stream['codec_name'] == 'ac3' and stream['disposition'].get('default', 0) == 1 or stream['index'] == 1]

                if len(video_streams) > 0 and len(audio_streams) > 0:
                    output_file = os.path.splitext(filename)[0] + '.mp4'
                    self.remove_list.append(output_file)

                    current_time = datetime.now().strftime(__data_format__)
                    c.execute('INSERT INTO ConversionTasks (films_id, status, start_time) VALUES (?, ?, ?)', (films_id, 'converting', current_time))
                    conn.commit()

                    try:
                        self.run_ffmpeg(filename, output_file)

                        current_time = datetime.now().strftime(__data_format__)
                        success, check_result = self.check_integrity(output_file)
                        if success:
                            c.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE films_id=?', ('done', current_time, check_result, films_id))
                            c.execute('UPDATE ConversionTasks SET new_filename=? WHERE films_id=?', (output_file, films_id))
                            conn.commit()
                            os.remove(filename)
                        else:
                            c.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE films_id=?', (check_result, current_time, check_result, films_id))
                            conn.commit()

                            os.remove(output_file)

                    except Exception as e:
                        current_time = datetime.now().strftime(__data_format__)
                        error_messege = str(e)
                        logging.error(f'{filename}: {error_messege}')
                        c.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE films_id=?', (error_messege, current_time, films_id))
                        conn.commit()
                        os.remove(output_file)

        conn.close()


if __name__ == '__main__':
    db_file = '/opt/film_storage.db'
    strat_films = ConvertTask('4096k', '192k')
    strat_films.convert_films(db_file)
