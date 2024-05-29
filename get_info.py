import sqlite3
import json
import os
import subprocess


def get_video_info_in_directory(directory):
    video_files = []
    subdirectories = []
    for root, dirs, files in os.walk(directory):
        if root[-2:] in ("/A", "/0", "/1", "/2", "/3", "/4", "/5", "/6", "/7", "/8", "/9",
                         "/B", "/C", "/D", "/E", "/F", "/G", "/H", "/I", "/J", "/K",
                         "/L", "/M", "/N", "/O", "/P", "/Q", "/R", "/S", "/T", "/U",
                         "/V", "/W", "/X", "/Y", "/Z"):
            for file in files:
                if file.endswith(('.mp4', '.avi', '.mkv')):  #delete
                    file_path = os.path.join(root, file)
                    video_files.append(file_path)
                    video_info = run_ffprobe(file_path)
                    if video_info:
                        streams = streams_data(video_info)
                        try:
                            save_to_films_table(video_info, streams)
                        except sqlite3.Error as e:
                            print(f"Error saving data: {e}")
                            
            for subdir in dirs:
                subdir_path = os.path.join(root, subdir)
                if os.path.isdir(subdir_path):
                    for sub_root, sub_dirs, sub_files in os.walk(subdir_path):
                        for sub_file in sub_files:
                            if sub_file.endswith(('.mp4', '.avi', '.mkv')): #delete
                                sub_file_path = os.path.join(sub_root, sub_file)
                                video_info = run_ffprobe(sub_file_path)
                                if video_info:
                                    streams = streams_data(video_info)
                                    try:
                                        save_to_serials_table(video_info, streams)
                                    except sqlite3.Error as e:
                                        print(f"Error saving data: {e}")
    return video_files, subdirectories


def run_ffprobe(file_path):
    command = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        print(f"Error running ffprobe for {file_path}: {result.stderr}")
        return None


def streams_data(data):
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


def save_to_films_table(data, streams):
    with sqlite3.connect('/opt/film_storage.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Films WHERE filename = ?', (data['format']['filename'],))
        count = cur.fetchone()
        if count is None:
            cur.execute("""INSERT INTO Films (filename, nb_streams, size, bit_rate, streams) 
                        VALUES (?, ?, ?, ?, ?)""", 
                        (data['format']['filename'], data['format']['nb_streams'], 
                        data['format']['size'], data['format']['bit_rate'], json.dumps(streams)))
            conn.commit()
        else:
            print(f"Data already exists for {data['format']['filename']}")

def save_to_serials_table(data, streams):
    with sqlite3.connect('/opt/film_storage.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Serials WHERE filename = ?', (data['format']['filename'],))
        count = cur.fetchone()
        if count is None:
            cur.execute("""INSERT INTO Serials (filename, nb_streams, size, bit_rate, streams) 
                        VALUES (?, ?, ?, ?, ?)""", 
                        (data['format']['filename'], data['format']['nb_streams'], 
                        data['format']['size'], data['format']['bit_rate'], json.dumps(streams)))
            conn.commit()
        else:
            print(f"Data already exists for {data['format']['filename']}")

if __name__ == "__main__":
    directory_path = "/file_storage/film_storage/"
    video_files, subdirectories = get_video_info_in_directory(directory_path)