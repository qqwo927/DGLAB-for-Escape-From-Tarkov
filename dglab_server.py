import asyncio
import base64
import contextlib
import io
import random
import socket
from pathlib import Path

import psutil
import qrcode
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pydglab_ws import DGLabWSServer, Channel, StrengthOperationType

from config import ConfigManager
from game_monitor import GameMonitor
from models import GameState
import pulses

class WebConfigData(BaseModel):
    LocalIP: str
    PowerLimit: int
    Ratelimit: float
    BagColorMin: list[int]
    BagColorMax: list[int]
    RoleHmax: float
    RoleHmin: float
    RoleSmax: float
    # 为了兼容前端，这里只列出部分字段，实际上可以扩展
    
class StartServerRequest(BaseModel):
    ip_address: str

class DGLabApp:
    """
    封装 FastAPI 应用，包含 DGLab 服务器控制功能
    """
    
    def __init__(self, cfg: ConfigManager):
        self.app = FastAPI()
        self.cfg = cfg
        
        # 游戏监视器
        self.monitor = GameMonitor(cfg)
        
        # 服务器状态
        self.dglab_server_task = None
        self.dglab_server_running = False
        self.game_detection_task = None
        
        # 二维码相关
        self.qrcode_data = None
        self.qrcode_url = None
        self.qrcode_ready = asyncio.Event()
        
        # 游戏状态 (用于前端显示)
        self.game_status = GameState.DISPLAY_NOT_STARTED
        self.game_power = 0
        self.game_hp = 0
        self.is_connected = False
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/networks")
        async def get_networks():
            """获取网络列表"""
            addrs = psutil.net_if_addrs()
            candidates = []
            for iface_name, iface_addrs in addrs.items():
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET:
                        ip_str = addr.address
                        if not (ip_str.startswith("127.") or ip_str.startswith("169.254")):
                            candidates.append({
                                "iface_name": iface_name,
                                "ip_str": ip_str
                            })
            return candidates

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """返回网卡选择页面"""
            html_file = Path(__file__).parent / "index.html"
            if html_file.exists():
                return html_file.read_text(encoding="utf-8")
            return HTMLResponse(content="<h1>index.html 文件未找到</h1>", status_code=404)

        @self.app.get("/dglab/waves")
        async def get_waves():
            """获取所有可用波形名称"""
            waves = ["custom"]
            if pulses:
                waves.extend(list(pulses.PULSE_DATA.keys()))
            return waves

        @self.app.get("/dglab/config")
        async def get_config():
            """获取配置"""
            return {
                "PowerLimit": self.cfg.PowerLimit,
                "Ratelimit": self.cfg.Ratelimit,
                "BagColorMin": self.cfg.BagColorMin,
                "BagColorMax": self.cfg.BagColorMax,
                "RoleHmax": self.cfg.RoleHmax,
                "RoleHmin": self.cfg.RoleHmin,
                "RoleSmax": self.cfg.RoleSmax,
                "RoleSmin": self.cfg.RoleSmin,
                "RoleVMax": self.cfg.RoleVMax,
                "RoleVMin": self.cfg.RoleVMin,
                "tempRate": self.cfg.tempRate,
                "HPlow": self.cfg.HPlow,
                "HPhigh": self.cfg.HPhigh,
                "WaveName": self.cfg.WaveName
            }
        
        @self.app.post("/dglab/config")
        async def update_config(config_data: dict):
            """更新配置"""
            try:
                # 分离 Basic 和 Advanced 配置
                basic_keys = ['PowerLimit', 'Ratelimit', 'HPlow', 'HPhigh']
                advanced_keys = ['BagColorMin', 'BagColorMax', 'RoleHmax', 'RoleHmin', 
                               'RoleSmax', 'RoleSmin', 'RoleVMax', 'RoleVMin', 'tempRate']
                
                # 转换类型并更新
                basic_update = {}
                for k in basic_keys:
                    if k in config_data:
                        basic_update[k] = float(config_data[k])
                
                if basic_update:
                    self.cfg.update_basic(**basic_update)
                
                advanced_update = {}
                for k in advanced_keys:
                    if k in config_data:
                        # 数组类型不做 float 转换，其他做 float
                        if k in ['BagColorMin', 'BagColorMax']:
                            advanced_update[k] = config_data[k]
                        else:
                            advanced_update[k] = float(config_data[k])
                
                # 特殊处理 RoleHsv 组合更新 (为了兼容 ConfigManager 的 save 逻辑)
                # ConfigManager.update_advanced 会自动处理 RoleHsvmax/min 的组合保存
                # 这里我们需要确保如果有单项更新，能正确保存到 list
                
                # 重新构建 HSV 列表以触发 ConfigManager 的保存逻辑
                current_h_max = advanced_update.get('RoleHmax', self.cfg.RoleHmax)
                current_s_max = advanced_update.get('RoleSmax', self.cfg.RoleSmax)
                current_v_max = advanced_update.get('RoleVMax', self.cfg.RoleVMax)
                advanced_update['RoleHsvmax'] = [current_h_max, current_s_max, current_v_max]
                
                current_h_min = advanced_update.get('RoleHmin', self.cfg.RoleHmin)
                current_s_min = advanced_update.get('RoleSmin', self.cfg.RoleSmin)
                current_v_min = advanced_update.get('RoleVMin', self.cfg.RoleVMin)
                advanced_update['RoleHsvmin'] = [current_h_min, current_s_min, current_v_min]

                if advanced_update:
                    self.cfg.update_advanced(**advanced_update)
                
                # 波形更新 - 恢复被用户删除的逻辑
                if "WaveName" in config_data:
                     self.cfg.update_wave_config(wave_name=config_data["WaveName"])

                return {"status": "success", "message": "配置已更新"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        @self.app.get("/dglab/start")
        async def start_dglab():
            if self.dglab_server_running:
                return {"status": "already_running", "message": "DGLab 服务器已在运行"}
            if await self.start_dglab_server():
                return {"status": "started", "message": "DGLab 服务器已启动"}
            return {"status": "error", "message": "启动失败"}
        
        @self.app.post("/dglab/start-with-ip")
        async def start_dglab_with_ip(request: StartServerRequest):
            if self.dglab_server_running:
                return {"status": "already_running", "message": "DGLab 服务器已在运行"}
            
            try:
                self.qrcode_ready.clear()
                self.qrcode_data = None
                self.qrcode_url = None
                self.is_connected = False
                
                if await self.start_dglab_server(ip_address=request.ip_address):
                    try:
                        await asyncio.wait_for(self.qrcode_ready.wait(), timeout=3.0)
                    except asyncio.TimeoutError:
                        pass
                    return {
                        "status": "started", 
                        "message": f"DGLab 服务器已启动，使用IP: {request.ip_address}\n波形没输出,按下第一个按钮打开波形输出",
                        "qrcode_data": self.qrcode_data,
                        "qrcode_url": self.qrcode_url
                    }
                return {"status": "error", "message": "启动失败"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        @self.app.get("/dglab/qrcode")
        async def get_qrcode():
            if not self.dglab_server_running:
                return {"status": "error", "message": "服务器未运行"}
            return {
                "status": "success",
                "qrcode_data": self.qrcode_data,
                "qrcode_url": self.qrcode_url
            }
        
        @self.app.get("/dglab/game-status")
        async def get_game_status():
            return {
                "status": self.game_status,
                "power": self.game_power,
                "hp": self.game_hp,
                "is_connected": self.is_connected
            }
        
        @self.app.get("/dglab/status")
        async def get_dglab_status():
            return {
                "running": self.dglab_server_running,
                "task_done": self.dglab_server_task.done() if self.dglab_server_task else None
            }

    async def start_dglab_server(self, ip_address: str = None):
        """启动服务器任务"""
        if self.dglab_server_running:
            return False
        try:
            self.dglab_server_task = asyncio.create_task(self.start_server(ip_address))
            self.dglab_server_running = True
            print("DGLab 服务器已启动")
            return True
        except Exception as e:
            print(f"启动 DGLab 服务器失败: {e}")
            return False

    async def stop_dglab_server(self):
        """停止服务器"""
        if not self.dglab_server_running:
            return False
        try:
            if self.game_detection_task and not self.game_detection_task.done():
                self.game_detection_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.game_detection_task
            if self.dglab_server_task and not self.dglab_server_task.done():
                self.dglab_server_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.dglab_server_task
            self.dglab_server_running = False
            print("DGLab 服务器已停止")
            return True
        except Exception as e:
            print(f"停止 DGLab 服务器失败: {e}")
            self.dglab_server_running = False
            return False

    def get_free_port(self, start=5678, end=8765):
        for _ in range(100):
            port = random.randint(start, end)
            with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                if s.connect_ex(('0.0.0.0', port)) != 0:
                    return port
        return start

    def generate_qrcode_base64(self, url: str):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        im = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        
        buffer = io.BytesIO()
        im.save(buffer, format='PNG')
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

    async def _process_game_loop(self, iteration_count=1):
        """处理一次游戏状态检测循环 (对应原代码中的一段逻辑)"""
        await asyncio.sleep(self.cfg.Ratelimit)
        
        # 使用 run_in_executor 在线程池中运行截图和图像处理，避免阻塞 asyncio 事件循环
        loop = asyncio.get_running_loop()
        power, state, hp = await loop.run_in_executor(None, self.monitor.process_screenshot)
        
        # 更新内部状态
        if iteration_count == 1:
            self.cfg.gamestate = state
        else:
            self.cfg.gamestate2 = state

        target_power = 0
        
        if state == GameState.GAME:
            self.cfg.power = power
            target_power = power
            self.game_status = GameState.DISPLAY_GAME
        elif state == GameState.BAG:
            # 保持 power 不变
            target_power = self.cfg.power
            self.game_status = GameState.DISPLAY_BAG
        else: # OTHER
            # 这里的逻辑有点微妙。原代码在 iteration 1 和 2 的处理略有不同
            # 如果是 Other，原代码会设为 0
            
            # 双重状态检查逻辑 (来自原代码)
            s1 = self.cfg.gamestate
            s2 = self.cfg.gamestate2
            
            # 这是一个近似的复现
            if s1 == GameState.GAME or s2 == GameState.GAME:
                 # 至少有一个是 Game，保持 Game 状态？
                 # 如果当前检测是 Other，但另一个是 Game，可能只是闪烁
                 if s1 == GameState.GAME and s2 == GameState.GAME:
                     # 确认为 Game
                     pass
                 elif state == GameState.OTHER:
                     # 当前是 Other，但有一个历史是 Game，这里原代码似乎会归零
                     target_power = 0
                     self.game_status = GameState.DISPLAY_NOT_ENTERED
            else:
                target_power = 0
                self.game_status = GameState.DISPLAY_NOT_ENTERED

        # 更新显示用的数据
        self.game_power = int(target_power)
        self.game_hp = hp
        
        # 发送指令
        if self.cfg.client:
            await self.cfg.client.set_strength(Channel.A, StrengthOperationType.SET_TO, int(target_power))

    async def send(self):
        """
        执行一次完整的检测周期 (包含两次截图，模拟原代码逻辑)
        """
        try:
            # 第一阶段
            await self._process_game_loop(1)
            
            # 第二阶段
            await self._process_game_loop(2)
            
        except Exception as e:
            print(f"Send loop error: {e}")

    async def _game_detection_loop(self):
        while True:
            try:
                await self.send()
            except asyncio.CancelledError:
                print("游戏检测循环已取消")
                raise
            except Exception as e:
                print(f"游戏检测循环错误: {e}")
                # 发生错误时稍作等待，避免快速重试导致资源浪费
                await asyncio.sleep(0.1)

    async def start_server(self, ip_address: str = None):
        """WebSocket 服务器主循环"""
        if ip_address:
            self.cfg.LocalIP = ip_address
            
        port = self.get_free_port()
        
        # 启动 DGLab WebSocket 服务
        # 增加心跳间隔(heartbeat_interval)和调整ping参数以避免超时
        # ping_interval: 默认为20秒，这里设为30
        # ping_timeout: 默认为20秒，这里设为60，给客户端更多响应时间
        async with DGLabWSServer("0.0.0.0", port, heartbeat_interval=60, ping_interval=30, ping_timeout=60) as server:
            self.cfg.client = server.new_local_client()
            
            # 生成二维码
            url = self.cfg.client.get_qrcode(f"ws://{self.cfg.LocalIP}:{port}")
            self.qrcode_url = url
            self.qrcode_data = self.generate_qrcode_base64(url)
            self.qrcode_ready.set()
            
            print("等待 App 扫码绑定...")
            await self.cfg.client.bind()
            
            self.is_connected = True
            print(f"已与 APP {self.cfg.client.target_id} 成功绑定")
            
            self.game_detection_task = asyncio.create_task(self._game_detection_loop())
            
            pulse_data_iterator = iter(self.cfg.PULSE_DATA.values())
            

            async for _ in self.cfg.client.data_generator():
                try:
                    # 发送波形 (如果启用)
                    pulse_data_current = next(pulse_data_iterator, None)
                    if not pulse_data_current:
                        # 循环波形
                        pulse_data_iterator = iter(self.cfg.PULSE_DATA.values())
                        pulse_data_current = next(pulse_data_iterator, None)
                    
                    if pulse_data_current:
                        await self.cfg.client.clear_pulses(Channel.A)
                        await self.cfg.client.clear_pulses(Channel.B)
                        await self.cfg.client.add_pulses(Channel.A, *(pulse_data_current))
                        await self.cfg.client.add_pulses(Channel.B, *(pulse_data_current))
                    
                    # 不加sleep 不知道为什么过一段时间就会停止发送波形,反正加了就没事了
                    await asyncio.sleep(0.01)
                        
                except Exception as e:
                    print(f"Error in main loop: {e}")
            
            if self.game_detection_task and not self.game_detection_task.done():
                self.game_detection_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.game_detection_task
