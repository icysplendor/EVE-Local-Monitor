import cv2
import numpy as np
import mss
import os

class VisionEngine:
    def __init__(self):
        self.local_templates = []
        self.overview_templates = []
        self.monster_templates = []
        
        self.template_status_msg = "初始化中..."
        self.last_screenshot_shape = "无"
        self.last_error = None
        
        self.debug_dir = os.path.join(os.getcwd(), "debug_scans")
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            
        self.load_templates()

    def load_templates(self):
        base_dir = os.getcwd()
        path_local = os.path.join(base_dir, "assets", "hostile_icons_local")
        path_overview = os.path.join(base_dir, "assets", "hostile_icons_overview")
        path_monster = os.path.join(base_dir, "assets", "monster_icons")
        
        self.local_templates = self._load_images_from_folder(path_local)
        self.overview_templates = self._load_images_from_folder(path_overview)
        self.monster_templates = self._load_images_from_folder(path_monster)
        
        self.template_status_msg = (
            f"路径: {base_dir}\n"
            f"本地图标: {len(self.local_templates)} 张\n"
            f"总览图标: {len(self.overview_templates)} 张\n"
            f"怪物图标: {len(self.monster_templates)} 张"
        )

    def _load_images_from_folder(self, folder):
        templates = []
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except:
                pass
            return templates
            
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.png', '.jpg', '.bmp')):
                path = os.path.join(folder, filename)
                try:
                    # 必须保留 Alpha 通道 (IMREAD_UNCHANGED)
                    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        # 如果是JPG没有透明通道，强制加一个全不透明的通道
                        if img.shape[2] == 3:
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                        templates.append(img)
                except:
                    pass
        return templates

    def capture_screen(self, region, debug_name=None):
        self.last_error = None
        if not region: 
            return None
        
        monitor = {"top": int(region[1]), "left": int(region[0]), "width": int(region[2]), "height": int(region[3])}
        
        try:
            with mss.mss() as sct:
                img = np.array(sct.grab(monitor))
                # mss 返回 BGRA
                # 为了后续处理方便，我们转为 BGR，因为归一化通常在 BGR 或 Gray 上做
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                h, w = img_bgr.shape[:2]
                self.last_screenshot_shape = f"{w}x{h}"
                
                if debug_name:
                    cv2.imwrite(os.path.join(self.debug_dir, f"debug_{debug_name}.png"), img_bgr)
                return img_bgr
                
        except Exception as e:
            self.last_error = f"截图失败: {str(e)}"
            return None

    def match_templates(self, screen_img, template_list, threshold, return_max_val=False):
        """
        参考用户提供的方案：回归 TM_CCOEFF_NORMED + 归一化预处理
        """
        if screen_img is None:
            err = self.last_error if self.last_error else "未获取到截图"
            return (err, 0.0) if return_max_val else False
            
        if not template_list:
            return ("无模板", 0.0) if return_max_val else False

        screen_h, screen_w = screen_img.shape[:2]
        
        # === 关键步骤 1: 截图归一化 ===
        # 将截图的对比度拉伸到 0-255，消除整体变灰/变亮的影响
        screen_norm = cv2.normalize(screen_img, None, 0, 255, cv2.NORM_MINMAX)
        
        max_score_found = 0.0
        all_skipped = True 

        for tmpl in template_list:
            tmpl_h, tmpl_w = tmpl.shape[:2]
            
            # 尺寸检查
            if screen_h < tmpl_h or screen_w < tmpl_w:
                continue 
            all_skipped = False 

            # 准备数据
            mask = None
            if tmpl.shape[2] == 4:
                # 移除 Alpha 通道，转为 BGR 用于归一化
                tmpl_bgr = cv2.cvtColor(tmpl, cv2.COLOR_BGRA2BGR)
                # 提取 Mask
                mask = tmpl[:, :, 3]
            else:
                tmpl_bgr = tmpl
            
            # === 关键步骤 2: 模板归一化 ===
            tmpl_norm = cv2.normalize(tmpl_bgr, None, 0, 255, cv2.NORM_MINMAX)

            try:
                # === 核心算法：TM_CCOEFF_NORMED ===
                # 使用归一化后的图片进行匹配
                if mask is not None:
                    res = cv2.matchTemplate(screen_norm, tmpl_norm, cv2.TM_CCOEFF_NORMED, mask=mask)
                else:
                    res = cv2.matchTemplate(screen_norm, tmpl_norm, cv2.TM_CCOEFF_NORMED)
                
                _, max_val, _, _ = cv2.minMaxLoc(res)
                
                if max_val > max_score_found:
                    max_score_found = max_val

            except Exception as e:
                # print(f"Error: {e}")
                continue

        if all_skipped:
            return ("尺寸错误", 0.0) if return_max_val else False

        if return_max_val:
            return (None, max_score_found)
        else:
            return max_score_found >= threshold
