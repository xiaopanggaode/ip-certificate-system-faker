@echo off
chcp 65001 >nul
echo ========================================
echo IP证书获取系统
echo ========================================
echo.
echo 正在启动服务器...
echo.
echo 启动成功后，请在浏览器中访问：
echo http://localhost:5000
echo.
echo 按 Ctrl+C 可以停止服务器
echo ========================================
echo.
python app.py
pause

