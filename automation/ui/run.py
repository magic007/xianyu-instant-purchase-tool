#!/usr/bin/env python
import os
import sys
import webbrowser
import time
from threading import Timer

# 添加项目根目录到路径，以便导入其他模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 使用8080端口避免与MacOS AirPlay冲突
PORT = 8080

def open_browser():
    """在默认浏览器中打开应用"""
    webbrowser.open(f'http://127.0.0.1:{PORT}/')

if __name__ == '__main__':
    # 检查是否安装了Flask
    try:
        from flask import Flask
    except ImportError:
        print("未检测到Flask库，正在安装...")
        import subprocess
        subprocess.call([sys.executable, "-m", "pip", "install", "flask"])
        print("Flask安装完成")
    
    # 导入应用 - 修复相对导入问题
    from automation.ui.app import app
    
    print("正在启动闲鱼秒拍搜索工具...")
    print("应用将在默认浏览器中打开")
    print(f"您也可以通过访问 http://127.0.0.1:{PORT} 或 http://[本机IP]:{PORT} 来使用")
    
    # 设置定时器，在应用启动后打开浏览器
    Timer(1.5, open_browser).start()
    
    # 启动Flask应用，监听所有接口
    app.run(debug=True, host='0.0.0.0', port=PORT) 