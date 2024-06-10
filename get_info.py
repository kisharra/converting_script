import sqlite3
import json
import os
import subprocess



def get_video_info_in_directory(directory):
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
                video_info = run_ffprobe(file_path)  #run ffprobe command
                if video_info:  #check if video info is not empty
                    streams = streams_data(video_info)  #transform streams data
                    try:
                        save_films(video_info, streams)  #save data to database
                    except sqlite3.Error as e:
                        print(f"Error saving data: {e}")
                            
            for subdir in dirs:  #iterate through subdirectories
                subdir_path = os.path.join(root, subdir)
                if os.path.isdir(subdir_path):
                    for sub_root, sub_dirs, sub_files in os.walk(subdir_path):
                        for sub_file in sub_files:
                            sub_file_path = os.path.join(sub_root, sub_file)
                            video_info = run_ffprobe(sub_file_path)
                            if video_info:
                                streams = streams_data(video_info)
                                try:
                                    save_serials(video_info, streams)
                                except sqlite3.Error as e:
                                    print(f"Error saving data: {e}")
    return video_files, subdirectories


def run_ffprobe(file_path, config):
    '''run ffprobe command'''
    command = [arg.format(file_path=file_path) for arg in config['ffprobe_command']]  #run ffprobe command which is in config
    result = subprocess.run(command, capture_output=True, text=True)  
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        print(f"Error running ffprobe for {file_path}: {result.stderr}")
        return None


def streams_data(data):
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


def save_films(data, streams):
    '''save film data to database'''
    with sqlite3.connect(config['db_file']) as conn:
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

def save_serials(data, streams):
    '''save serials data to database'''
    with sqlite3.connect(config['db_file']) as conn:
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

if __name__ == "__main__":
    with open ('config.json', 'r') as config_file:  #read config file
        config = json.load(config_file)
    directory_path = config['file_path']  #set directory path
    video_files, subdirectories = get_video_info_in_directory(directory_path)  #get video info in directory