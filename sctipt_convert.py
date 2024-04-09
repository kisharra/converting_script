import json
import subprocess
import os


def get_final_files(directory):
    final_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) >= 10737418240:
                final_files.append(file_path)
    return final_files

def extract_info(file_path):
    size = os.path.getsize(file_path)
    return {'FilePath': file_path, 'FileSize': size}


def save_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def convert_video(input_file, output_file):
    """Конвертирует видеофайл в формат MP4, оставляя только первую аудиодорожку и сохраняя разрешение"""
    command = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", "libx264",  # Используем кодек H.264 для видео  
        #"-crf", "26",  # Качество видео (меньше значение, лучше качество, больше размер)
        "-preset:v", "ultrafast",  # Устанавливаем скорость конвертирования 
        "-c:a:0", "aac",  # Кодируем первую аудиодорожку в AAC
        "-strict", "experimental",
        "-map", "0:v:0",  # Выбираем первую видеодорожку
        "-map", "0:a:0",  # Выбираем первую аудиодорожку
        "-movflags", "+faststart",  # Фрагментация конвертируемого файла
        "-b:v", "6000k",  # Устанавливаем максимальный размер видеофайла
        output_file
    ]
    subprocess.run(command)
    # os.remove(input_file)  # Удаляем исходный файл


def main(file_name):
    """main function"""
    directory = "/file_storage/film_storage/"  # Укажите путь к вашей директории здесь
    final_files = get_final_files(directory)
    
    file_info = []
    for file_path in final_files:
        file_info.append(extract_info(file_path))
    
    save_to_json(file_info, "/file_storage/work_scripts/file_info.json")
    
    for info in file_info:
        input_file = info['FilePath']
        output_file = os.path.splitext(input_file)[0] + ".mp4"
        info["CurrentFileStatus"] = "Конвертация"  # Добавляем информацию о текущем статусе файла
        
        with open('file_info.json', 'w', encoding='utf-8') as file:
            json.dump(file_info, file, ensure_ascii=False, indent=4)

        convert_video(input_file, output_file)

        info["CurrentFileStatus"] = f"Файл конвертирован"  # Обновляем информацию о статусе файла
        info["NewFilePath"] = output_file  # Добавляем новый путь к конвертированному файлу
        with open('file_info.json', 'w', encoding='utf-8') as file:
            json.dump(file_info, file, ensure_ascii=False, indent=4)

    with open('file_info.json', 'w', encoding='utf-8') as file:
        json.dump(file_info, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main('file_info.json')