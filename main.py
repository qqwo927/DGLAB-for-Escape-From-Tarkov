import uvicorn
from config import ConfigManager
from dglab_server import DGLabApp
import random
import contextlib
import socket
import webbrowser

def get_free_port(start=5678, end=8765):
    for _ in range(100):
        port = random.randint(start, end)
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            if s.connect_ex(('0.0.0.0', port)) != 0:
                return port
    return start

if __name__ == "__main__":
    # 创建全局配置管理器实例 (自动加载配置)
    cfg = ConfigManager()

    print("Starting DGLab Server...")
    print(f"Loaded config from {cfg.config_file}")

    # 初始化应用
    app = DGLabApp(cfg)
    port = get_free_port()
    print(f"Serving on port {port} ...")

    # 自动在浏览器中打开对应端口的地址
    webbrowser.open(f"http://127.0.0.1:{port}")

    # 启动 Web 服务
    uvicorn.run(app.app, host="0.0.0.0", port=port)
