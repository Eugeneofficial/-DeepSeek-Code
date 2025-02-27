@echo off
echo Starting DeepSeek Code Companion Installer (By Abramov)...
echo ==============================================

:: Настраиваемые переменные
set BASE_OLLAMA_PORT=11434
set APP_PORT=7860
set DEEPSEEK_MODEL=deepseek-r1:1.5b
set DEFAULT_MODEL_DIR=%USERPROFILE%\.ollama\models
set MODEL_DIR=%DEFAULT_MODEL_DIR%

:: Запрос директории для моделей
set /p MODEL_DIR="Enter directory for Ollama models (press Enter for default: %DEFAULT_MODEL_DIR%): "
if "%MODEL_DIR%"=="" set MODEL_DIR=%DEFAULT_MODEL_DIR%
echo Model directory set to: %MODEL_DIR%

:: Создание директории, если её нет
if not exist "%MODEL_DIR%" (
    mkdir "%MODEL_DIR%"
    if errorlevel 1 (
        echo Error: Could not create directory %MODEL_DIR%. Please run as administrator.
        pause
        exit /b
    )
)

:: Установка переменной окружения для Ollama
set OLLAMA_MODELS=%MODEL_DIR%
setx OLLAMA_MODELS "%MODEL_DIR%" >nul 2>&1

:: Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.8+ is not installed. Please install it from python.org and add to PATH.
    pause
    exit /b
)

:: Проверка Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Git is not installed. Please install it from git-scm.com and add to PATH.
    pause
    exit /b
)

:: Клонирование репозитория
echo Cloning DeepSeek Code Companion repository...
if exist deepseek-r1-chat (
    cd deepseek-r1-chat
    git pull origin main
) else (
    git clone https://github.com/Eugeneofficial/-DeepSeek-Code
    cd deepseek-r1-chat
)

:: Установка зависимостей
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies. Check your internet connection or Python setup.
    pause
    exit /b
)

:: Проверка и установка Ollama
echo Checking for Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama not found. Downloading and installing Ollama...
    powershell -Command "Invoke-WebRequest -Uri https://ollama.com/download/win/ollama-setup.exe -OutFile ollama-setup.exe"
    if exist ollama-setup.exe (
        ollama-setup.exe /silent
        del ollama-setup.exe
    ) else (
        echo Error: Failed to download Ollama. Please install it manually from ollama.com.
        pause
        exit /b
    )
)

:: Проверка порта Ollama
set OLLAMA_PORT=%BASE_OLLAMA_PORT%
:CHECK_PORT
netstat -aon | findstr :%OLLAMA_PORT% >nul 2>&1
if %errorlevel% equ 0 (
    echo Warning: Port %OLLAMA_PORT% is in use. Trying next port...
    set /a OLLAMA_PORT+=1
    goto CHECK_PORT
)
set OLLAMA_HOST=127.0.0.1:%OLLAMA_PORT%

:: Запуск Ollama
echo Starting Ollama service on port %OLLAMA_PORT%...
start /b "" ollama serve
timeout /t 5 >nul

:: Проверка модели
echo Checking for %DEEPSEEK_MODEL%...
ollama list | findstr %DEEPSEEK_MODEL% >nul 2>&1
if %errorlevel% neq 0 (
    echo Model not found. Pulling %DEEPSEEK_MODEL%...
    ollama pull %DEEPSEEK_MODEL%
    if %errorlevel% neq 0 (
        echo Warning: Failed to pull model. You can download it later via the interface.
    )
)

:: Запуск приложения
echo Launching DeepSeek Code Companion on port %APP_PORT%...
python app.py --server_port %APP_PORT% --share
if %errorlevel% neq 0 (
    echo Error: Failed to launch the app. Check the console for details.
    pause
    exit /b
)

echo Installation complete! Open http://127.0.0.1:%APP_PORT% or the shared URL.
echo Models are saved in: %MODEL_DIR%
pause