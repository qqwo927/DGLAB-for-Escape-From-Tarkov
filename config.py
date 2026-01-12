import configparser
import ast
from typing import List, Tuple, Any
from models import AppConfig, RuntimeState, GameState
import json
import pulses

class ConfigManager:
    """统一管理所有配置变量"""
    
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 屏幕设置常量 (原代码硬编码了2K分辨率参数)
        # x_start, y_start, width, height
        self.Set2K = [int(2560*0.014), int(1440*0.02), int(2560*0.048), int(1440*0.2)]
        self.ScreenSet = self.Set2K
        
        # 核心配置数据模型
        self.data = AppConfig()
        
        # 运行时状态
        self.runtime = RuntimeState()
        
        # 兼容旧代码的属性访问 (通过 __getattr__ 实现或显式定义)
        # 为了IDE提示友好，这里显式定义属性，指向 self.data 或 self.runtime
        
        # 初始化配置
        self._init_config()
        
    def _init_config(self):
        """初始化配置文件"""
        self.config.read(self.config_file)
        
        if not self.config.sections():
            self._create_default_config()
            self.config.read(self.config_file)
        
        self._load_from_config()
        self._init_pulse_data()

    def _create_default_config(self):
        """创建默认配置文件"""
        self.config['Basic'] = {
            'LocalIP': '111.111.111.111',
            'PowerLimit': '60',
            'Ratelimit': '0.4',
            'HPlow': '100',
            'HPhigh': '435'
        }
        self.config['Advanced'] = {
            'BagColorMin': '[39,49,66]',
            'BagColorMax': '[43,53,70]',
            'RoleHsvmax': '[130,1,0.6]',
            'RoleHsvmin': '[0,0.4,0.1]',
            'tempRate': '0.3'
        }
        
        # 默认波形数据
        default_wave = [
            ((11, 11, 11, 11), (100, 100, 100, 100)), ((11, 11, 11, 11), (20, 20, 20, 20)),
            ((11, 11, 11, 11), (100, 100, 100, 100)), ((11, 11, 11, 11), (100, 100, 100, 100)),
            ((11, 11, 11, 11), (40, 40, 40, 40)), ((11, 11, 11, 11), (95, 95, 95, 95)),
            ((11, 11, 11, 11), (100, 100, 100, 100)), ((20, 20, 20, 20), (50, 50, 50, 50)),
            ((20, 20, 20, 20), (0, 0, 0, 0)), ((20, 20, 20, 20), (50, 50, 50, 50)),
            ((20, 20, 20, 20), (100, 100, 100, 100)), ((20, 20, 20, 20), (100, 100, 100, 100)),
            ((20, 20, 20, 20), (50, 50, 50, 50)), ((20, 20, 20, 20), (0, 0, 0, 0)),
            ((20, 20, 20, 20), (50, 50, 50, 50)), ((20, 20, 20, 20), (100, 100, 100, 100)),
            ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),
            ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),
            ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),
            ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),
            ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),
            ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100))
        ]
        self.config['Wave'] = {
            'wave': str(default_wave),
            'wavename': 'custom'
        }
        
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        print("Created Default Config File")

    def _load_from_config(self):
        """从配置文件加载变量"""
        # Basic
        self.data.LocalIP = self.config.get("Basic", "LocalIP", fallback=self.data.LocalIP)
        self.data.PowerLimit = self.config.getfloat("Basic", "PowerLimit", fallback=self.data.PowerLimit)
        self.data.Ratelimit = self.config.getfloat("Basic", "Ratelimit", fallback=self.data.Ratelimit)
        self.data.HPlow = self.config.getfloat("Basic", "HPlow", fallback=self.data.HPlow)
        self.data.HPhigh = self.config.getfloat("Basic", "HPhigh", fallback=self.data.HPhigh)

        # Advanced
        try:
            self.data.BagColorMin = self._parse_list(self.config.get("Advanced", "BagColorMin"))
            self.data.BagColorMax = self._parse_list(self.config.get("Advanced", "BagColorMax"))
            
            role_hsv_max = self._parse_list(self.config.get("Advanced", "RoleHsvmax"))
            self.data.RoleHmax = role_hsv_max[0]
            self.data.RoleSmax = role_hsv_max[1]
            self.data.RoleVMax = role_hsv_max[2]
            
            role_hsv_min = self._parse_list(self.config.get("Advanced", "RoleHsvmin"))
            self.data.RoleHmin = role_hsv_min[0]
            self.data.RoleSmin = role_hsv_min[1]
            self.data.RoleVMin = role_hsv_min[2]
            
            self.data.tempRate = self.config.getfloat("Advanced", "tempRate", fallback=self.data.tempRate)
        except Exception as e:
            print(f"Error loading Advanced config: {e}")

        # Wave
        try:
            self.data.Wave = self._parse_list(self.config.get("Wave", "wave"))
        except Exception as e:
            print(f"Error loading Wave config: {e}")
            self.data.Wave = []
            
        self.data.WaveName = self.config.get("Wave", "wavename", fallback="custom")

    def _parse_list(self, value_str: str) -> list:
        """安全解析列表字符串"""
        try:
            return ast.literal_eval(value_str)
        except (ValueError, SyntaxError):
            # Fallback for simple cases if needed, or re-raise
            return eval(value_str) # 为了兼容性保留 eval，但仅作为后备

    def _init_pulse_data(self):
        """初始化脉冲数据"""
        # 优先使用 WaveName 指定的预设波形
        if pulses and self.data.WaveName != "custom" and self.data.WaveName in pulses.PULSE_DATA:
            self.runtime.pulse_data = {'wave': pulses.PULSE_DATA[self.data.WaveName]}
        else:
            # 否则使用自定义波形
            self.runtime.pulse_data = {'wave': self.data.Wave}

    def save(self, include_runtime=False):
        """保存配置到文件"""
        # 更新 ConfigParser 对象
        self.config.set('Basic', 'LocalIP', str(self.data.LocalIP))
        self.config.set('Basic', 'PowerLimit', str(self.data.PowerLimit))
        self.config.set('Basic', 'Ratelimit', str(self.data.Ratelimit))
        self.config.set('Basic', 'HPlow', str(self.data.HPlow))
        self.config.set('Basic', 'HPhigh', str(self.data.HPhigh))
        
        self.config.set('Advanced', 'BagColorMin', str(self.data.BagColorMin))
        self.config.set('Advanced', 'BagColorMax', str(self.data.BagColorMax))
        self.config.set('Advanced', 'RoleHsvmax', str([self.data.RoleHmax, self.data.RoleSmax, self.data.RoleVMax]))
        self.config.set('Advanced', 'RoleHsvmin', str([self.data.RoleHmin, self.data.RoleSmin, self.data.RoleVMin]))
        self.config.set('Advanced', 'tempRate', str(self.data.tempRate))
        
        self.config.set('Wave', 'wave', str(self.data.Wave))
        self.config.set('Wave', 'wavename', str(self.data.WaveName))

        # Runtime 不建议保存，但为了兼容接口保留参数
        if include_runtime:
            pass # 我们不再保存 Runtime 到 config.ini，这通常是不需要的

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def save_without_runtime(self):
        self.save(include_runtime=False)

    def update_basic(self, **kwargs):
        """更新基础配置"""
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)
        self.save()

    def update_advanced(self, **kwargs):
        """更新高级配置"""
        # 特殊处理 RoleHsv 组合
        if 'RoleHsvmax' in kwargs:
             val = kwargs.pop('RoleHsvmax') # 假设是 list
             if isinstance(val, (list, tuple)) and len(val) >= 3:
                 self.data.RoleHmax, self.data.RoleSmax, self.data.RoleVMax = val
        
        if 'RoleHsvmin' in kwargs:
             val = kwargs.pop('RoleHsvmin')
             if isinstance(val, (list, tuple)) and len(val) >= 3:
                 self.data.RoleHmin, self.data.RoleSmin, self.data.RoleVMin = val

        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)
        self.save()
        
    def update_wave(self, wave):
        """兼容旧接口"""
        self.data.Wave = wave
        self.data.WaveName = "custom" # 既然手动更新了波形数据，就自动切回 custom
        self._init_pulse_data()
        self.save()
        
    def update_wave_config(self, wave_name: str = None, wave_data: list = None):
        """更新波形配置的新接口"""
        if wave_name:
            self.data.WaveName = wave_name
        if wave_data:
            self.data.Wave = wave_data
            self.data.WaveName = "custom" # 如果提供了数据，强制切回 custom
            
        self._init_pulse_data()
        self.save()

    def reload(self):
        self.config.read(self.config_file)
        self._load_from_config()
        self._init_pulse_data()

    # 属性代理，为了兼容旧代码直接访问 cfg.LocalIP 等
    def __getattr__(self, name):
        if hasattr(self.data, name):
            return getattr(self.data, name)
        if hasattr(self.runtime, name):
            return getattr(self.runtime, name)
        # 特殊兼容
        if name == "PULSE_DATA":
            return self.runtime.pulse_data
        if name == "Enable":
            return 1 if self.runtime.enable else 0
        raise AttributeError(f"'ConfigManager' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # 允许直接设置属性
        if name in ['config_file', 'config', 'Set2K', 'ScreenSet', 'data', 'runtime']:
            super().__setattr__(name, value)
            return
            
        if hasattr(self.data, name):
            setattr(self.data, name, value)
            # 注意：这里没有自动 save，与原代码行为一致（原代码直接设值也不自动 save，除了 update_* 方法）
        elif hasattr(self.runtime, name):
            setattr(self.runtime, name, value)
        elif name == "Enable":
            self.runtime.enable = bool(value)
        elif name == "PULSE_DATA":
             self.runtime.pulse_data = value
        else:
             super().__setattr__(name, value)
