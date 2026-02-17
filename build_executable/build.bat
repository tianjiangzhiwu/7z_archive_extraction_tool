@echo off
echo 清理旧的构建文件...
rd /s /q "dist" "build" 2>nul

echo 开始打包应用...
pyinstaller --clean ArchiveExtractor.spec

if %errorlevel% == 0 (
    echo.
    echo 打包成功！
    echo 可执行文件位置: dist\ArchiveExtractor\ArchiveExtractor.exe
    pause
) else (
    echo.
    echo 打包失败！
    pause
)