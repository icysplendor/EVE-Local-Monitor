import time
import threading
import requests
import os
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class AlarmWorker(QObject):
    # 信号通知主界面及日志，参数为日志文本
    log_signal = pyqtSignal(str)

    def __init__(self, config_manager, vision_engine):
        super().__init__()
        self.cfg = config_manager
        self.vision = vision_engine
        self.running = False
        self.thread = None
        
        # 状态矩阵：记录当前是否检测到威胁
        self.status = {
            "local": False,
            "overview": False,
            "monster": False
        }

    def start(self):
        """启动后台检测线程"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        """停止后台检测线程"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        """主检测循环"""
        while self.running:
            # 获取当前时间戳 (用于日志显示)
            now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # 1. 动态获取最新的配置参数
            regions = self.cfg.get("regions")
            t_hostile = self.cfg.get("thresholds")["hostile"]
            t_monster = self.cfg.get("thresholds")["monster"]

            # 2. 截图
            # 如果区域未设置，capture_screen 返回 None
            img_local = self.vision.capture_screen(regions.get("local"))
            img_overview = self.vision.capture_screen(regions.get("overview"))
            img_monster = self.vision.capture_screen(regions.get("monster"))

            # 3. 匹配并获取分数 (return_max_val=True)
            # 返回格式: (是否匹配成功(Bool), 最高相似度分数(Float))
            is_local, score_local = self.vision.match_templates(img_local, self.vision.hostile_templates, t_hostile, True)
            is_overview, score_overview = self.vision.match_templates(img_overview, self.vision.hostile_templates, t_hostile, True)
            is_monster, score_monster = self.vision.match_templates(img_monster, self.vision.monster_templates, t_monster, True)

            # 更新内部状态
            self.status["local"] = is_local
            self.status["overview"] = is_overview
            self.status["monster"] = is_monster

            # 4. 决策逻辑 (优先级系统)
            has_threat = is_local or is_overview
            sound_to_play = None
            
            # 优先级判断：
            # 1. 如果既有威胁(本地/总览) 且 正在打怪 -> 混合报警 (最危险，可能被怪留住)
            # 2. 总览威胁 -> 总览报警 (距离最近)
            # 3. 本地威胁 -> 本地报警 (预警)
            # 4. 只有怪物 -> 怪物报警 (正常打怪)
            if has_threat and is_monster:
                sound_to_play = "mixed"
            elif is_overview:
                sound_to_play = "overview"
            elif is_local:
                sound_to_play = "local"
            elif is_monster:
                sound_to_play = "monster"

            # 5. 生成详细状态描述字串
            # 格式: [L:1(0.95) | O:0(0.12) | M:0(0.00)]
            # L=Local, O=Overview, M=Monster, 括号内为相似度得分
            status_desc = (f"[L:{int(is_local)}({score_local:.2f}) | "
                           f"O:{int(is_overview)}({score_overview:.2f}) | "
                           f"M:{int(is_monster)}({score_monster:.2f})]")
            
            if sound_to_play:
                # 触发报警分支
                log_msg = f"[{now_str}] ⚠️ 触发报警: {sound_to_play.upper()} {status_desc}"
                self.log_signal.emit(log_msg)
                
                # 触发 Webhook (异步，防止阻碍主循环)
                webhook_url = self.cfg.get("webhook_url")
                if webhook_url:
                    try:
                        threading.Thread(target=requests.post, args=(webhook_url,), kwargs={'json':{'alert': sound_to_play}}).start()
                    except:
                        pass
                
                # 报警状态下休眠较长时间，模拟等待音频播放完毕，避免日志刷屏过快
                time.sleep(2.0)
            else:
                # 安全巡逻分支
                log_msg = f"[{now_str}] ✅ 安全 {status_desc}"
                self.log_signal.emit(log_msg)
                
                # 正常的快速轮询间隔 (例如 0.5秒)
                time.sleep(0.5)
