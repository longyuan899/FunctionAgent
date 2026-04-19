@echo off
chcp 65001 >nul
echo ==========================================
echo   智能任务代理系统 启动中...
echo ==========================================
echo.
echo  访问地址: http://localhost:8001
echo  API文档:  http://localhost:8001/docs
echo.
echo  安装依赖: pip install -r requirements.txt
echo ==========================================
python main.py
pause
