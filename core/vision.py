import cv2
import numpy as np
import mss
import os

class VisionEngine:
    def __init__(self):
        self.sct = mss.mss()
        self.hostile_templates = []
        self.monster_templates = []
        self.load_templates()

    def load_templates(self):
        self.hostile_templates = self._load_images_from_folder("assets/hostile_icons")
        self.monster_templates = self._load_images_from_folder("assets/monster_icons")

    def _load_images_from_folder(self, folder):
        templates = []
        if not os.path.exists(folder):
            os.makedirs(folder)
            return templates
            
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.png', '.jpg', '.bmp')):
                path = os.path.join(folder, filename)
                # 读取原图 (可能包含Alpha通道)
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    templates.append(img)
        return templates

    def capture_screen(self, region):
        # region: [x, y, w, h]
        if not region: return None
        # mss截取区域必须要整数
        monitor = {
            "top": int(region[1]), 
            "left": int(region[0]), 
            "width": int(region[2]), 
            "height": int(region[3])
        }
        try:
            img = np.array(self.sct.grab(monitor))
            # MSS返回 BGRA，转为 BGR 方便OpenCV处理
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"截图失败: {e}")
            return None

    def match_templates(self, screen_img, template_list, threshold, return_max_val=False):
        """
        return_max_val: 如果为True，返回 (Bool, max_val) 用来调试
        """
        if screen_img is None or not template_list:
            return (False, 0.0) if return_max_val else False

        screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
        
        max_score_found = 0.0

        for tmpl in template_list:
            tmpl_h, tmpl_w = tmpl.shape[:2]
            
            # 屏幕截图比模板还小，不可能匹配成功，直接跳过
            if screen_gray.shape[0] < tmpl_h or screen_gray.shape[1] < tmpl_w:
                continue

            # 处理透明通道
            mask = None
            if tmpl.shape[2] == 4:
                # 拆分通道: B, G, R, Alpha
                b, g, r, a = cv2.split(tmpl)
                # 将原来的BGRA转为灰度用于匹配内容
                # 注意：这里需要先把前3个通道合成为BGR再转Gray，否则cvtColor会报错
                tmpl_bgr = cv2.merge([b, g, r])
                tmpl_gray = cv2.cvtColor(tmpl_bgr, cv2.COLOR_BGR2GRAY)
                mask = a # 使用Alpha通道作为掩码
            else:
                tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)

            try:
                # 核心修正：传入 mask 参数
                # 注意：TM_CCOEFF_NORMED 支持 mask，但要求 screen 和 temp 大小关系正确
                if mask is not None:
                    res = cv2.matchTemplate(screen_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED, mask=mask)
                else:
                    res = cv2.matchTemplate(screen_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val > max_score_found:
                    max_score_found = max_val
                
                if max_val >= threshold:
                    if not return_max_val:
                        return True
            except Exception as e:
                # 某些情况下尺寸不匹配会报错，忽略该模板
                print(f"匹配错误: {e}")
                continue

        if return_max_val:
            return (max_score_found >= threshold, max_score_found)
        else:
            return False
