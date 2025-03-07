#!/usr/bin/env python
"""
CheckCo 系统启动脚本
此脚本会启动服务器并自动打开浏览器前端页面
"""

import os
import sys
import time
import webbrowser
import subprocess
import platform
import threading

def check_dependencies():
    """检查并安装所需依赖"""
    try:
        import http.server
        import json
        import urllib.parse
        
        # 尝试导入可能需要额外安装的包
        try:
            import langchain_together
            import langgraph
        except ImportError:
            print("正在安装所需依赖包...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                  "langchain-together", "langgraph-core"])
            print("依赖安装完成！")
    except ImportError as e:
        print(f"错误: 缺少必要的依赖 - {e}")
        print("请确保Python环境正确安装")
        sys.exit(1)

def start_server():
    """直接在当前进程中启动服务器"""
    # 导入服务器模块
    print("正在启动服务器...")
    
    try:
        # 方法1: 直接导入server.py中的run函数并在新线程中运行
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import server
        
        # 创建一个线程来运行服务器
        server_thread = threading.Thread(target=server.run)
        server_thread.daemon = True  # 设置为守护线程，这样主程序退出时它也会退出
        server_thread.start()
        
        return server_thread
    except ImportError:
        print("无法导入server模块，尝试使用子进程方式启动...")
        # 方法2: 如果导入失败，使用子进程方式但确保输出重定向到当前控制台
        process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # 行缓冲
        )
        
        # 创建一个线程实时读取并显示服务器输出
        def output_reader():
            for line in process.stdout:
                print(f"[Server] {line.strip()}")
        
        reader_thread = threading.Thread(target=output_reader)
        reader_thread.daemon = True
        reader_thread.start()
        
        return process

def open_browser():
    """打开浏览器前端页面"""
    # 获取当前脚本的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建前端HTML文件的路径
    html_path = os.path.join(current_dir, "front.html")
    
    # 检查文件是否存在
    if not os.path.exists(html_path):
        print(f"错误: 找不到前端文件 {html_path}")
        return False
    
    # 将文件路径转换为URL格式
    file_url = f"file://{html_path}"
    if platform.system() == "Windows":
        file_url = file_url.replace("\\", "/")
    
    print(f"正在打开浏览器: {file_url}")
    webbrowser.open(file_url)
    return True

def main():
    """主函数"""
    print("CheckCo 系统启动中...")
    
    # 检查依赖
    check_dependencies()
    
    # 启动服务器
    server_process = start_server()
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(3)
    
    # 打开浏览器
    if not open_browser():
        print("无法打开前端页面，请手动打开front.html文件")
    
    print("\nCheckCo 系统已启动!")
    print("服务器运行在: http://localhost:8000")
    print("前端页面已在浏览器中打开")
    print("按 Ctrl+C 停止服务器")
    
    try:
        # 保持主程序运行，直到用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止服务器...")
        if isinstance(server_process, subprocess.Popen):
            server_process.terminate()
        print("系统已关闭")

if __name__ == "__main__":
    main()