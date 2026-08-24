# Делаю из изображений видео с частотой одно изображения в секунду.
# Формат mkv
# Добавляю в субтитры названия файлов.
# После создания субтитров с оригинальнымы названиями, переименовываю файл изображения в 4-х значные номера по порядку: 0000.jpg, 0001.jpg, 0002.jpg, ...
# После создания видео переименовываю обратно в оригинальные имена

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

file_video = "!output.mkv"
dir_shots = ''
file_ffmpeg_list = '!filelist.txt'

def ffmpeg_convert():
    # ffmpeg.exe -hide_banner -hwaccel cuda -f concat -safe 0 -i {file_ffmpeg_list} -scodec copy  -max_interleave_delta 0 {file_video}''')
    result = subprocess.run(
        f'''ffmpeg.exe -hide_banner -hwaccel cuda -f concat -safe 0 -i {file_ffmpeg_list} -scodec copy -c copy {file_video}''')
    return True if result.returncode == 0 else False


def subfolders():
    """
        Конвертирование во всех подпапках,
        кроме подпапки с текущим дней.
    """
    workdir = Path(__file__).parent.absolute()
    date_now = datetime.now().date().isoformat()
    file_list = []
    for d in Path(dir_shots).glob('*'):
        dpath = workdir.joinpath(d)
        if (filev:=d.joinpath(file_video)).is_file():
            print(filev)
            file_list.append(f"file '{filev.as_posix()}'")
    print(file_list)
    if file_list:
        with open(file_ffmpeg_list, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_list))
        ffmpeg_convert()

if __name__ == '__main__':
    # main()
    subfolders()
