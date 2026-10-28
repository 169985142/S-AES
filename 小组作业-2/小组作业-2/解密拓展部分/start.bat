@echo off
chcp 936 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_ENTRY=main.py"
set "REQ_FILE=requirements.txt"
set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%APP_ENTRY%" goto :NO_ENTRY

if exist "%VENV_PY%" (
    set "PYTHON=%VENV_PY%"
    goto :CHECK_PYQT
)

where python >nul 2>nul
if errorlevel 1 goto :NO_PYTHON

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if errorlevel 1 goto :OLD_PYTHON

python -c "import PyQt5" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=python"
    goto :RUN
)

echo [提示] 系统 Python 未安装 PyQt5，正在创建本地虚拟环境...
python -m venv .venv
if errorlevel 1 goto :VENV_FAIL
set "PYTHON=%VENV_PY%"
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :INSTALL_FAIL
"%PYTHON%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 goto :INSTALL_FAIL

:CHECK_PYQT
"%PYTHON%" -c "import PyQt5" >nul 2>nul
if errorlevel 1 (
    echo [提示] 正在安装项目依赖...
    "%PYTHON%" -m pip install -r "%REQ_FILE%"
    if errorlevel 1 goto :INSTALL_FAIL
)

:RUN
"%PYTHON%" "%APP_ENTRY%" %*
set "EXIT_CODE=%errorlevel%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo [错误] 程序异常退出，错误码 %EXIT_CODE%。
    pause
)
endlocal
exit /b 0

:NO_ENTRY
echo.
echo [错误] 未找到程序入口 main.py。
pause
exit /b 1

:NO_PYTHON
echo.
echo [错误] 未找到 Python。请安装 Python 3.9+ 并勾选 Add to PATH。
pause
exit /b 1

:OLD_PYTHON
echo.
echo [错误] Python 版本过低，需要 3.9+。
pause
exit /b 1

:VENV_FAIL
echo.
echo [错误] 创建 .venv 失败。
pause
exit /b 1

:INSTALL_FAIL
echo.
echo [错误] 依赖安装失败。请检查网络，或删除 .venv 后重试。
pause
exit /b 1