# Прохожусь по подпапкам в директории `dir_shots`.
# В каждой подпапке делаю из изображений видео с частотой одно изображения в секунду.
# Формат mkv.
# Требуется установленный ffmpeg.
# Добавляю в субтитры названия файлов.
# После создания субтитров с оригинальнымы названиями, переименовываю файлы изображений в 4-х значные номера по порядку: 0000.jpg, 0001.jpg, 0002.jpg, ...
# После создания видео переименовываю изображения обратно в оригинальные имена.

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

# временный файл субтитров
file_srt = '!output.srt'
# файл видео
file_video = "!output.mkv"
# маска изображений для видео
files_mask = '*.jpg'
# временный файл переименовывания файлов изображений
file_renaming_map = "!renaming_map.json"
# папка с подпапками изображений. Если поставить '', то будет искать подпапки в текущий директории.
dir_shots = 'sshots/'

# команда ffmpeg конвертирование изображений в видеофайл
# %04d.jpg - формат файлов изображений типа: 0000.jpg, 0001.jpg, 0002.jpg, ...
ffmpeg_cmd = f'''ffmpeg -hide_banner -framerate 1 -i %04d.jpg -i !output.srt -max_interleave_delta 0 {file_video}'''
# Пример установки принудительного размера видео и отключения масштабирования.
# ffmpeg_cmd =  f'''ffmpeg -framerate 1 -i %04d.jpg -i !output.srt -max_interleave_delta 0 -vf "scale=5120:1600:force_original_aspect_ratio=decrease,pad=5120:1600:-1:-1,setsar=1" {file_video}'''


def convert_ffmpeg():
    """
        Запускаю ffmpeg в текущей папке.
        Конвертирую изображения в видеофайл
    """
    result = subprocess.run(ffmpeg_cmd)
    return True if result.returncode == 0 else False


def create_srt(lines: list):
    """
     create subtitle file 
     one line - one second

    """
    with open(file_srt, 'w') as f:
        for idx, line in enumerate(lines):
            f.write(f'{idx + 1}\n')
            timestamp1 = timedelta(seconds=idx)
            f.write(f"{timestamp1},000 --> {timestamp1},999\n")
            f.write(f"{line}\n\n")


def rename_files():
    """
    Переименовываю файлы для ffmpeg 
    в 4-х значные номера по порядку: 0000.jpg, 0001.jpg, 0002.jpg, ...
    и возвращаю карту переименований
    list of{
         'src': file,
         'dst': file_new
         }

    :return: list of dict
    """
    print('Rename files.')
    renaming_map = []
    for idx, file in enumerate(Path().glob(files_mask)):
        file_new = f'{idx:04}{file.suffix}'
        # every name of file will be used in subtitles
        renaming_map.append(
            {'src': file,
             'dst': file_new
             })
        file.rename(file_new)
    return renaming_map


def save_renaming_map(renaming_map):
    with open(file_renaming_map, 'w', encoding='utf-8') as f:
        # ensure_ascii - не экранировать не аски символы (русские  символы)
        json.dump([{'src': str(i['src']), 'dst': str(i['dst'])} for i in renaming_map], f, indent=2, ensure_ascii=False)


def read_renaming_map():
    try:
        with open(file_renaming_map, 'r', encoding='utf-8') as f:
            data_json = json.loads(f.read())
    except IOError:
        return None
    else:
        return data_json


def rename_files_back(renaming_map):
    """
        По карте переименований переименовываю файлы обратно
    """
    print('Rename files back.')
    for f in renaming_map:
        Path(f['dst']).rename(f['src'])


def check_renaming():
    renaming_map = read_renaming_map()
    if renaming_map and Path(renaming_map[0]['dst']).exists():
        print('Files are renamed already!')
        return renaming_map


def convert_current_folder():
    """
    create video file in current directory
    """
    if Path(file_video).exists():
        print(f"File '{file_video}' exists")
        return
        rewrite = input(f"File '{file_srt}' exists. Rewrite file? [y/N]: ")
        if rewrite.lower() != 'y':
            return
    # сначала проверяю, если уже было переименование и не было переименования обратно из-за прерывания программы
    # 
    renaming_map = check_renaming() or rename_files()
    print(f"Files {len(renaming_map)}")
    # create subtitles by file names
    if renaming_map:
        create_srt([i['src'] for i in renaming_map])
        save_renaming_map(renaming_map)
    convert_ffmpeg()
    rename_files_back(renaming_map)


def convert_subfolders():
    """
        Конвертирование во всех подпапках,
        кроме подпапки текущего дня.
    """
    workdir = Path(__file__).parent.absolute()
    date_now = datetime.now().date().isoformat()
    for d in Path(dir_shots).glob('*'):
        dpath = workdir.joinpath(d)
        print(dpath)
        if date_now not in str(d) and dpath.is_dir():
            os.chdir(dpath)
            convert_current_folder()


if __name__ == '__main__':
    convert_subfolders()
