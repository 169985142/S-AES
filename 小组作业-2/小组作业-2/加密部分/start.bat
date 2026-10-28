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
    echo 请查看上方错误信息；如需帮助，请保留本窗口内容。
    pause
)
endlocal
exit /b 0

:NO_ENTRY
echo.
echo [错误] 未找到程序入口 main.py。
echo 请确认 start.bat 与 main.py 位于同一目录。
pause
endlocal
exit /b 1

:NO_PYTHON
echo.
echo [错误] 未找到 Python。
echo 请安装 Python 3.9 或更高版本，并勾选“Add Python to PATH”。
pause
endlocal
exit /b 1

:OLD_PYTHON
echo.
echo [错误] Python 版本过低，本项目需要 Python 3.9 或更高版本。
echo 请升级 Python 后重试。
pause
endlocal
exit /b 1

:VENV_FAIL
echo.
echo [错误] 创建 .venv 失败。
echo 请检查当前目录是否可写，或在命令行执行：
echo   python -m venv .venv
pause
endlocal
exit /b 1

:INSTALL_FAIL
echo.
echo [错误] 依赖安装失败。
echo 请检查网络连接，或手动执行：
echo   "%PYTHON%" -m pip install -r "%REQ_FILE%"
pause
endlocal
exit /b 1
