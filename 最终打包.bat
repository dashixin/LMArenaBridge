@echo off
chcp 65001 >nul
echo ========================================
echo   LMArenaBridge 最终打包工具
echo ========================================
echo.
echo 使用已验证的命令进行打包
echo.

REM 运行最终打包脚本
python final_pack.py

echo.
pause
