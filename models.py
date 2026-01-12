from enum import Enum
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field

class GameState(str, Enum):
    GAME = "game"
    BAG = "bag"
    OTHER = "other"
    # 前端显示的中文状态
    DISPLAY_GAME = "游戏中"
    DISPLAY_BAG = "在背包"
    DISPLAY_NOT_ENTERED = "未进入游戏"
    DISPLAY_NOT_STARTED = "未启动"

class AppConfig(BaseModel):
    # Basic
    LocalIP: str = "111.111.111.111"
    PowerLimit: float = 60.0
    Ratelimit: float = 0.4
    HPlow: float = 100.0
    HPhigh: float = 435.0
    
    # Advanced
    BagColorMin: List[int] = [39, 49, 66]
    BagColorMax: List[int] = [43, 53, 70]
    RoleHmax: float = 130.0
    RoleHmin: float = 0.0
    RoleSmax: float = 1.0
    RoleSmin: float = 0.4
    RoleVMax: float = 0.6
    RoleVMin: float = 0.1
    tempRate: float = 0.3
    
    # Wave
    WaveName: str = "custom" # "custom" 表示使用 Wave 字段的自定义数据，否则对应 pulses.py 中的键
    Wave: List[Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]] = Field(default_factory=list)

class RuntimeState:
    def __init__(self):
        self.power: int = 0
        self.temp: float = 440.0
        self.gamestate: GameState = GameState.OTHER
        self.gamestate2: GameState = GameState.OTHER
        self.hp: float = 440.0
        self.enable: bool = False
        self.client = None
        self.pulse_data = None
