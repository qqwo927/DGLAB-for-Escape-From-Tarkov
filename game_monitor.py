import numpy as np
import pyautogui
from typing import Tuple, Optional
from models import GameState, RuntimeState

class GameMonitor:
    def __init__(self, config_manager):
        self.cfg = config_manager
        # 预计算常量
        self.BASE_PIXELS = 35136
        self.MSK = [2030, 11527, 11951, 16595, 17017, 23127, 24322]
        self.CW = [0.0795, 0.1931, 0.1363, 0.1363, 0.1591, 0.1477, 0.1477]
        self.DLIST = None
        self.LI = None
        
        # 缓存屏幕设置以便检测变更
        self._last_screenset = None

    def _update_constants(self):
        """如果屏幕设置改变，更新预计算的索引"""
        current_screenset = self.cfg.ScreenSet
        if self._last_screenset == current_screenset:
            return

        pointsnum = current_screenset[2] * current_screenset[3]
        
        # 重新计算 Dlist
        self.DLIST = [int((m / self.BASE_PIXELS) * pointsnum) for m in self.MSK]
        
        # 重新计算 Li (要保留的像素索引之外的所有索引)
        # 注意：原代码逻辑是 np.delete(all_indices, Dlist) -> 删除了 Dlist 里的索引？
        # 原代码：
        # Li=np.delete(np.array(range(0,35136)),Dlist)
        # points= np.delete(i_ar.reshape([-1,3]),Li,axis=0)
        # 解释：
        # 1. 创建 0..35135 的数组
        # 2. 从中删除 Dlist 中的索引 -> 得到 Li (包含了除 Dlist 以外的所有索引)
        # 3. 从图像数组中删除 Li 对应的行 -> 只剩下 Dlist 对应的行
        # 所以最终只取了 Dlist 指定的那几个像素。
        
        # 优化：直接取 Dlist 对应的像素即可，不需要创建巨大的 Li 数组然后 delete。
        # 原代码逻辑非常低效。
        # i_ar.reshape([-1,3])[Dlist] 即可。
        
        self._last_screenset = current_screenset

    @staticmethod
    def rgb2hsv(r: float, g: float, b: float) -> Tuple[float, float, float]:
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        m = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            if g >= b:
                h = ((g-b)/m)*60
            else:
                h = ((g-b)/m)*60 + 360
        elif mx == g:
            h = ((b-r)/m)*60 + 120
        elif mx == b:
            h = ((r-g)/m)*60 + 240
        else: # mx == b
            h = ((r-g)/m)*60 + 240
            
        if mx == 0:
            s = 0
        else:
            s = m/mx
        v = mx
        return h, s, v

    def process_screenshot(self) -> Tuple[float, str, float]:
        """
        处理截图并返回计算出的 (power, status, hp)
        """
        self._update_constants()
        
        try:
            # 截图
            img = pyautogui.screenshot(region=self.cfg.ScreenSet)
            img_ar = np.array(img)
            
            # 提取关键点
            # 展平为 (pixels, 3)
            pixels = img_ar.reshape([-1, 3])
            
            # 提取特定像素点 (原代码逻辑的优化版)
            # 确保索引不越界
            valid_indices = [i for i in self.DLIST if i < len(pixels)]
            if not valid_indices:
                return 0, GameState.OTHER, 0

            selected_points = pixels[valid_indices]
            
            # 计算加权平均 RGB
            # 注意：如果提取的点数量不对，权重数组可能需要调整？
            # 原代码是固定的 7 个点。如果 DLIST 长度是 7，CW 长度也是 7，没问题。
            
            # 容错：如果 selected_points 少于 7 个 (极端情况)，截断 CW
            weights = self.CW[:len(selected_points)]
            
            rgb_avg = np.average(selected_points, axis=0, weights=weights)
            
            # 计算 HSV
            hss = self.rgb2hsv(rgb_avg[0], rgb_avg[1], rgb_avg[2])
            
            # 判定逻辑
            power = 0
            
            # 1. 判定是否在游戏中 (检查 HSV 范围)
            h, s, v = hss
            if (self.cfg.RoleHmin <= h < self.cfg.RoleHmax and
                self.cfg.RoleSmax > s >= self.cfg.RoleSmin and
                self.cfg.RoleVMin <= v < self.cfg.RoleVMax):
                
                # 计算 HP
                x1 = (h/360.0) * (s * v)
                # 拟合公式
                ps = (258597.6*(x1**3) - 75978.385*(x1**2) + 9241.92*x1 + 0.05899) + 7
                
                # 平滑处理
                current_hp = ps * self.cfg.tempRate + self.cfg.temp * (1 - self.cfg.tempRate)
                self.cfg.temp = current_hp # 更新缓存
                self.cfg.hp = current_hp
                
                # 计算强度
                if current_hp >= self.cfg.HPhigh: # 以前是 430，配置默认 435，原代码行 391 用 self.cfg.HPhigh，行 474 用 430... 统一用配置
                    power = 0
                else:
                    if current_hp >= 0:
                        # 线性插值
                        power = self.cfg.PowerLimit * ((440 - current_hp) / (440 - self.cfg.HPlow))
                    else:
                        power = self.cfg.PowerLimit
                
                # 限制最大强度
                power = min(power, self.cfg.PowerLimit)
                
                return power, GameState.GAME, current_hp

            # 2. 判定是否在背包 (检查单个点的 RGB 范围？原代码用的是 points[0])
            # 原代码: 
            # elif(self.cfg.BagColorMin[0]<points[0][0]<self.cfg.BagColorMax[0])...
            # points[0] 是 selected_points[0]
            first_point = selected_points[0]
            if (self.cfg.BagColorMin[0] < first_point[0] < self.cfg.BagColorMax[0] and
                self.cfg.BagColorMin[1] < first_point[1] < self.cfg.BagColorMax[1] and
                self.cfg.BagColorMin[2] < first_point[2] < self.cfg.BagColorMax[2]):
                
                # 背包状态保持原有强度？
                # 原代码: self.cfg.power = self.cfg.power (保持不变)
                return self.cfg.power, GameState.BAG, self.cfg.hp

            # 3. 其他状态
            return 0, GameState.OTHER, 0

        except Exception as e:
            print(f"Screenshot processing error: {e}")
            return 0, GameState.OTHER, 0

