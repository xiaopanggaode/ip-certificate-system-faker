@echo off
chcp 65001 >nul
echo ========================================
echo IP证书获取系统 - 依赖安装工具
echo ========================================
echo.
echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python！
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

echo Python环境正常
echo.
echo 正在安装依赖包...
echo.
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 安装失败，请检查网络连接或手动安装
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 现在可以运行 run.bat 启动应用
echo 按任意键退出...
pause >nul

