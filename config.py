# config.py

import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class Config:
    # папка с подпапками изображений
    dir_shots: str = 'sshots'

    # выходные файлы
    file_video: str = '!output.mkv'
    file_srt: str = '!output.srt'
    file_renaming_map: str = '!renaming_map.json'

    # изображения
    files_mask: str = '*.jpg'

    # ffmpeg
    ffmpeg: str = 'ffmpeg.exe'
    ffmpeg_video_encoder: str = "libx264"
    ffmpeg_input_framerate: int = 1

    def find_ffmpeg(self, app_dir: Path) -> str:
        """
        Ищу ffmpeg рядом с программой.
        Если не найден — использую ffmpeg из PATH.
        """

        local_ffmpeg = app_dir / self.ffmpeg

        if local_ffmpeg.is_file():
            return str(local_ffmpeg)

        ffmpeg = shutil.which('ffmpeg')

        if ffmpeg:
            return str(Path(ffmpeg).resolve())

        raise FileNotFoundError(
            'ffmpeg не найден рядом с программой '
            'и не найден в PATH.'
        )


def get_app_dir() -> Path:
    """
    Папка программы:
      - рядом с exe для PyInstaller
      - рядом с .py для обычного запуска
    """

    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
CONFIG_FILE = APP_DIR / 'config.json'


def save_config(config: Config) -> None:
    """
    Сохраняю конфигурацию в config.json
    """

    with CONFIG_FILE.open('w', encoding='utf-8') as f:
        json.dump(
            asdict(config),
            f,
            indent=2,
            ensure_ascii=False
        )


def load_config() -> Config:
    """
    Загружаю конфигурацию.
    Если файла нет — создаю его с настройками по умолчанию.
    """

    if not CONFIG_FILE.exists():
        cfg = Config()
        save_config(cfg)
        return cfg

    with CONFIG_FILE.open('r', encoding='utf-8') as f:
        data = json.load(f)

    return Config(**data)
