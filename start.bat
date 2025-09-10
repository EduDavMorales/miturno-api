@echo off
title MiTurno API
echo.
echo ==========================================
echo           MITURNO API
echo ==========================================
echo.
echo Iniciando servicios Docker...

docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ API iniciada correctamente!
    echo.
    echo 🌐 API: http://localhost:8000
    echo 📚 Docs: http://localhost:8000/docs
    echo 🩺 Health: http://localhost:8000/health
    echo.
    echo Para parar: docker-compose down
) else (
    echo.
    echo ❌ Error al iniciar la API
    echo Verifica que Docker Desktop este corriendo
)

echo.
pause