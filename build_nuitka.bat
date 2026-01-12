@echo off

python -m nuitka --version
if errorlevel 1 (
    pip install nuitka
)

set BUILD_DIR=build
set DIST_DIR=dist
set MAIN_FILE=main.py
set OUTPUT_NAME=EFT-DG

echo ========================================
echo 开始使用 Nuitka 编译...
echo ========================================

python -m nuitka ^
    --standalone ^
    --onefile ^
    --jobs=16 ^
    --windows-console-mode=force ^
    --enable-plugin=numpy ^
    --include-package=pydglab_ws ^
    --include-package=qrcode ^
    --include-package=PIL ^
    --include-package-data=qrcode ^
    --include-package-data=PIL ^
    --include-data-file=index.html=index.html ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=scipy ^
    --output-dir=%DIST_DIR% ^
    --output-filename=%OUTPUT_NAME%.exe ^
    --remove-output ^
    --show-progress ^
    --show-memory ^
    %MAIN_FILE%



echo ========================================
echo 构建完成！
echo ========================================
pause

