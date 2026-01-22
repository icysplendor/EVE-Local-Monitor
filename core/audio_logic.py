import time
import threading
import requests
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class AlarmWorker(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, config_manager, vision_engine):
        super().__init__()
        self.cfg = config_manager
        self.vision = vision_engine
        self.running = False
        self.thread = None
        self.status = {"local": False, "overview": False, "monster": False}

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        while self.running:
            now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            regions = self.cfg.get("regions")
            t_hostile = self.cfg.get("thresholds")["hostile"]
            t_monster = self.cfg.get("thresholds")["monster"]

            # 调试名称
            img_local = self.vision.capture_screen(regions.get("local"), "local")
            img_overview = self.vision.capture_screen(regions.get("overview"), "overview")
            img_monster = self.vision.capture_screen(regions.get("monster"), "monster")

            # 匹配
            is_local, score_local = self.vision.match_templates(img_local, self.vision.hostile_templates, t_hostile, True)
            # 获取 local 匹配时的错误
            err_local = self.vision.last_error 
            
            is_overview, score_overview = self.vision.match_templates(img_overview, self.vision.hostile_templates, t_hostile, True)
            err_overview = self.vision.last_error

            is_monster, score_monster = self.vision.match_templates(img_monster, self.vision.monster_templates, t_monster, True)
            err_monster = self.vision.last_error

            self.status["local"] = is_local
            self.status["overview"] = is_overview
            self.status["monster"] = is_monster

            # 报警逻辑
            has_threat = is_local or is_overview
            sound_to_play = None
            if has_threat and is_monster: sound_to_play = "mixed"
            elif is_overview: sound_to_play = "overview"
            elif is_local: sound_to_play = "local"
            elif is_monster: sound_to_play = "monster"

            # === 构建带错误诊断的日志 ===
            def fmt_score(score, err):
                if score == 0.0 and err:
                    return f"❌{err}" # 如果是0分且有错，显示错误原因
                return f"{score:.2f}"

            status_desc = (f"[L:{int(is_local)}({fmt_score(score_local, err_local)}) | "
                           f"O:{int(is_overview)}({fmt_score(score_overview, err_overview)}) | "
                           f"M:{int(is_monster)}({fmt_score(score_monster, err_monster)})]")
            
            if sound_to_play:
                log_msg = f"[{now_str}] ⚠️ 触发: {sound_to_play.upper()} {status_desc}"
                self.log_signal.emit(log_msg)
                
                webhook = self.cfg.get("webhook_url")
                if webhook:
                    try:
                        threading.Thread(target=requests.post, args=(webhook,), kwargs={'json':{'alert':sound_to_play}}).start()
                    except: pass
                time.sleep(2.0)
            else:
                log_msg = f"[{now_str}] ✅ 安全 {status_desc}"
                self.log_signal.emit(log_msg)
                time.sleep(0.5)
