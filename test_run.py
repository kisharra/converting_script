import json
import subprocess
from get_info import streams_data
from get_info import run_ffprobe

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
input_file = '/file_storage/film_storage/A/A.Good.Year.2006.Hybrid.1080p.Open.Matte.BLUEBIRD.mkv'
output_file = '/file_storage/film_storage/A/A.Good.Year.2006.Hybrid.1080p.Open.Matte.BLUEBIRD.mp4'
# bitrate = config['bitrate_video_film']
# b_a = config['bitrate_audio']
# command_ffmpeg = [arg.format(input_file=input_file, output_file=output_file, b_v=bitrate, b_a=b_a) for arg in config['ffmpeg_command']]
# result = subprocess.run(command_ffmpeg)
video_info = run_ffprobe(input_file, config)
if video_info:
    streams = streams_data(video_info)
    print(streams)