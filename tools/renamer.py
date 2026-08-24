# Переименовывает файлы jpg в текущей или указанной директории
# формат имени файла: `shot '%Y-%m-%d %H%M%S.jpg`
# Дата Время - дата время изменения файла
# пример: `shot 2026-06-13 182853.jpg`

import sys
from pathlib import Path
from datetime import datetime

folder = Path('')  # поменяйте на нужную папку или передайте через argv
if len(sys.argv) > 1:
    folder = Path(sys.argv[1])


def get_file_modification_time(path: Path) -> datetime:
    stat = path.stat()
    ts = stat.st_mtime
    return datetime.fromtimestamp(ts)


files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.jpg'])

for f in files:
    dt = get_file_modification_time(f)
    new_name = f"shot {dt.strftime('%Y-%m-%d %H%M%S')}{f.suffix.lower()}"
    target = f.with_name(new_name)
    if target.exists():
        # если уже есть файл с таким именем, добавляем индекс чтобы не потерять файлы
        base = dt.strftime('%Y-%m-%d %H%M%S')
        i = 1
        while True:
            candidate = f"shot {base}_{i}{f.suffix.lower()}"
            target = f.with_name(candidate)
            if not target.exists():
                break
            i += 1
    f.rename(target)
    print(f"Переименован: {f.name} -> {target.name}")
