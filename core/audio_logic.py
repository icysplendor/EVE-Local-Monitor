# ... (前面的引用不变)

    def _loop(self):
        while self.running:
            now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            regions = self.cfg.get("regions")
            t_hostile = self.cfg.get("thresholds")["hostile"]
            t_monster = self.cfg.get("thresholds")["monster"]

            # 截图
            img_local = self.vision.capture_screen(regions.get("local"))
            img_overview = self.vision.capture_screen(regions.get("overview"))
            img_monster = self.vision.capture_screen(regions.get("monster"))

            # 匹配并获取分数 (使用新增加的 return_max_val=True)
            # 这里的逻辑稍微改一下，为了拿分数调试
            is_local, score_local = self.vision.match_templates(img_local, self.vision.hostile_templates, t_hostile, True)
            is_overview, score_overview = self.vision.match_templates(img_overview, self.vision.hostile_templates, t_hostile, True)
            is_monster, score_monster = self.vision.match_templates(img_monster, self.vision.monster_templates, t_monster, True)

            self.status["local"] = is_local
            self.status["overview"] = is_overview
            self.status["monster"] = is_monster

            # ... (决策逻辑不变) ...
            has_threat = is_local or is_overview
            sound_to_play = None
            if has_threat and is_monster: sound_to_play = "mixed"
            elif is_overview: sound_to_play = "overview"
            elif is_local: sound_to_play = "local"
            elif is_monster: sound_to_play = "monster"

            # 修正后的日志输出：带上分数
            # %.2f 表示保留两位小数
            status_desc = (f"[L:{int(is_local)}({score_local:.2f}) | "
                           f"O:{int(is_overview)}({score_overview:.2f}) | "
                           f"M:{int(is_monster)}({score_monster:.2f})]")
            
            if sound_to_play:
                log_msg = f"[{now_str}] ⚠️ 触发报警: {sound_to_play.upper()} {status_desc}"
                self.log_signal.emit(log_msg)
                # ... (Webhook code 不变)
                time.sleep(2.0)
            else:
                log_msg = f"[{now_str}] ✅ 安全 {status_desc}"
                self.log_signal.emit(log_msg)
                time.sleep(0.5)
