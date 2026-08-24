# Прохожусь по подпапкам в директории `dir_shots`.
# В каждой подпапке делаю из изображений видео с частотой одно изображения в секунду.
# Формат mkv.
# Требуется установленный ffmpeg.
# Добавляю субтитры из имён файлов.
# После создания субтитров с оригинальными названиями,
# переименовываю файлы изображений в 4-х значные номера по порядку: 0000.jpg, 0001.jpg, 0002.jpg, ...
# После создания видео переименовываю изображения обратно в оригинальные имена.

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from config import APP_DIR, load_config

config = load_config()
ffmpeg = config.find_ffmpeg(APP_DIR)

print("APP_DIR =", APP_DIR)
print("FFMPEG =", ffmpeg)
print("DIR_SHOTS =", config.dir_shots)


def convert_ffmpeg(
        f_video: str | Path,
        f_srt: str | Path,
        frame_pattern: str = "%04d.jpg",
) -> bool:
    """
    Запускаю ffmpeg в текущей папке.
    Конвертирую изображения + субтитры в видеофайл.
    """
    f_video = Path(f_video)
    f_srt = Path(f_srt)

    if not any(Path.cwd().glob(frame_pattern.replace('%04d', '*'))):
        print("No input frames found.")
        return False

    if not f_srt.exists():
        print(f"Subtitle file not found: {f_srt}")
        return False
    # Пример установки принудительного размера видео и отключения масштабирования.
    # ffmpeg_cmd =  f'''ffmpeg -framerate 1 -i %04d.jpg -i !output.srt -max_interleave_delta 0 -vf "scale=5120:1600:force_original_aspect_ratio=decrease,pad=5120:1600:-1:-1,setsar=1" {file_video}'''
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-framerate", str(config.ffmpeg_input_framerate),
        "-i", frame_pattern,
        "-i", str(f_srt),
        "-max_interleave_delta", "0",
        "-c:v", config.ffmpeg_video_encoder,
        str(f_video)
    ]

    print("Running ffmpeg:")
    print(" ".join(f'"{arg}"' if " " in arg else arg for arg in cmd))

    try:
        result = subprocess.run(cmd, text=True)
    except FileNotFoundError:
        print(f"ffmpeg not found in PATH: {ffmpeg}")
        return False
    if result.returncode != 0:
        print(f"ffmpeg failed with exit code: {result.returncode}")
        return False

    return True


def format_srt_timestamp(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def create_srt(lines: list[str], file_srt: str | Path) -> None:
    """
    Создаю SRT-файл из списка имён файлов.
    Каждое изображение показывается 1 секунду.
    """

    file_srt = Path(file_srt)
    with file_srt.open('w', encoding='utf-8', newline='\n') as f:
        for idx, line in enumerate(lines):
            start = timedelta(seconds=idx)
            end = timedelta(seconds=idx + 1)
            f.write(f"{idx + 1}\n")
            f.write(f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n")
            f.write(f"{line}\n\n")


def rename_files(renaming_map: list[dict[str, str]]) -> None:
    """
    Переименовываю файлы для ffmpeg по карте renaming_map.
    В текущей директории.
    Карта:
        [
            {'src': 'image_a.jpg', 'dst': '0000.jpg'},
            {'src': 'image_b.jpg', 'dst': '0001.jpg'},
            ...
        ]
    """

    print('Rename files.')

    for row in renaming_map:
        Path(row['src']).rename(row['dst'])


def make_renaming_map() -> list[dict[str, str]]:
    """
    Переименовываю файлы для ffmpeg. В текущей директории.
    в 4-х значные номера по порядку: 0000.jpg, 0001.jpg, 0002.jpg, ...
    и возвращаю карту переименований
    list of{
         'src': file,
         'dst': file_new
         }

    :return: list of dict
    """

    print('Make renaming_map.')
    renaming_map: list[dict[str, str]] = []

    files = sorted(Path.cwd().glob(config.files_mask))

    if not files:
        print("No image files found.")
        return []

    for idx, file_original in enumerate(files):
        file_new = f'{idx:04d}{file_original.suffix}'
        renaming_map.append(
            {'src': str(file_original),
             'dst': file_new
             })
    return renaming_map


def save_renaming_map(renaming_map: list[dict[str, str]]) -> None:
    """
    Сохраняю карту переименований.
    """

    with open(config.file_renaming_map, 'w', encoding='utf-8') as f:
        # ensure_ascii - не экранировать не аски символы (русские  символы)
        json.dump(renaming_map, f, indent=2, ensure_ascii=False)


def read_renaming_map() -> list[dict[str, str]] | None:
    """
    Загружаю карту переименований.
    """

    try:
        with open(config.file_renaming_map, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return None


def rename_files_back(renaming_map: list[dict[str, str]]) -> None:
    """
    По карте переименований восстанавливаю оригинальные имена файлов.
    """

    for f in renaming_map:
        Path(f['dst']).rename(f['src'])


def check_renaming() -> list[dict[str, str]]:
    """
    Проверяю, осталась ли карта незавершённого переименования.
    """

    renaming_map = read_renaming_map()
    if renaming_map and Path(renaming_map[0]['dst']).exists():
        return renaming_map
    return []


def convert_current_folder() -> None:
    """
    Создаю видео файл в текущей директории
    """

    # сначала проверяю, если уже было переименование и не было переименования обратно из-за прерывания программы
    #
    renaming_map = check_renaming()

    if renaming_map:
        print('Found unfinished file renaming.')
    else:
        renaming_map = make_renaming_map()

    if not renaming_map:
        print("No files to process.")
        return

    print(f"Files {len(renaming_map)}")
    save_renaming_map(renaming_map)
    rename_files(renaming_map)

    # create subtitles by file names
    create_srt(
        [Path(i['src']).name for i in renaming_map],
        config.file_srt
    )
    try:
        # Создаём видео.
        success = convert_ffmpeg(
            config.file_video,
            config.file_srt,
        )
        if not success:
            print("Video conversion failed.")
    finally:
        # В любом случае восстанавливаем оригинальные имена.
        rename_files_back(renaming_map)


def convert_subfolders() -> None:
    """
    Конвертирую все подпапки из config.dir_shots,
    кроме подпапки текущего дня.
    """

    date_now = datetime.now().date().isoformat()

    original_cwd = Path.cwd()

    shots_dir = APP_DIR / config.dir_shots

    if not shots_dir.exists():
        print(f"Directory not found: {shots_dir}")
        return

    for dpath in sorted(shots_dir.iterdir()):

        if not dpath.is_dir():
            continue

        # Не обрабатываем текущий день.
        if date_now in dpath.name:
            print(f"Skip current day: {dpath}")
            continue

        print()
        print(f"Processing: {dpath}")

        video_file = dpath / config.file_video

        if video_file.exists():
            print(
                f"File '{config.file_video}' already exists."
            )

            # Если программа была прервана после переименования.
            try:
                os.chdir(dpath)
                rename_files_back(
                    check_renaming()
                )
            finally:
                os.chdir(original_cwd)

            continue

        try:
            os.chdir(dpath)

            convert_current_folder()

        except Exception as e:
            print(
                f"Error processing {dpath}: {e}",
                file=sys.stderr,
            )

        finally:
            os.chdir(original_cwd)

    os.chdir(original_cwd)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Создание MKV-видео из последовательности JPG с субтитрами из имён файлов."
    )

    parser.add_argument(
        "folder",
        nargs="?",
        help=f'Папка для обработки. Если не указана, обрабатываются подпапки из {config.dir_shots or "текущей директории"}.'
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.folder:
        dpath = Path(args.folder)
        print(f"Processing: {dpath}")

        if not dpath.is_dir():
            print(
                f"Directory not found: {dpath}",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            os.chdir(dpath)
            convert_current_folder()
        except Exception as e:
            print(
                f"Error: {e}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        convert_subfolders()


if __name__ == '__main__':
    main()
