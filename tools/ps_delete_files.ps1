# chcp 65001
# chcp меняет кодовую страницу консоли (ввод/вывод для консольных программ), но не автоматически меняет .NET-потоки в PowerShell; для PowerShell корректнее явно установить:
[Console]::OutputEncoding = [Text.Encoding]::UTF8
[Console]::InputEncoding  = [Text.Encoding]::UTF8

#  Удаляет файлы  '*.jpg', '*.json', '*.srt' в подпапках, кроме текущей
$todayDir = Get-Date -Format 'yyyy-MM-dd'

$root = '.'   # замените на ваш корень
$exts = '.jpg','.json','.srt'

Get-ChildItem -Path $root -Directory -Recurse | ForEach-Object {
    $dir = $_.FullName
    if ($_.Name -like $todayDir) { return }    # исключаем директорию с текущей датой
    if (Test-Path -LiteralPath (Join-Path $dir '!output.mkv')) {
        Write-Output "=== Содержимое: $dir ==="
        Get-ChildItem -LiteralPath $dir -File |
            Where-Object { $_.Extension -in $exts } |
            #ForEach-Object { $_.Name }
            Remove-Item
    }
}