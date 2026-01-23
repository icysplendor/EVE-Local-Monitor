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
        
        # 初始化 CLAHE
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            
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
                    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                    if img is not None:
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
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                h, w = img_bgr.shape[:2]
                self.last_screenshot_shape = f"{w}x{h}"
                
                # 不再保存硬盘，直接返回内存对象
                return img_bgr
                
        except Exception as e:
            self.last_error = f"截图失败: {str(e)}"
            return None

    def gamma_correction(self, img, gamma=1.5):
        """
        Gamma 校正：
        Gamma > 1.0 会让暗部更暗，亮部保持。
        这能有效压制归一化带来的背景噪点。
        """
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(img, table)

    def match_templates(self, screen_img, template_list, threshold, return_max_val=False):
        if screen_img is None:
            err = self.last_error if self.last_error else "未获取到截图"
            return (err, 0.0) if return_max_val else False
            
        if not template_list:
            return ("无模板", 0.0) if return_max_val else False

        screen_h, screen_w = screen_img.shape[:2]
        
        # === 优化步骤 1: 动态范围检查 ===
        screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
        min_val, max_val, _, _ = cv2.minMaxLoc(screen_gray)
        
        # 如果画面最亮和最暗的差值小于 30 (说明画面灰蒙蒙一片，或者纯黑)
        # 此时强制归一化会把噪点放大成信号，必须跳过
        if (max_val - min_val) < 30:
             return ("对比度过低", 0.0) if return_max_val else False

        # === 优化步骤 2: 归一化 + Gamma 压制 ===
        # 先归一化拉伸
        screen_norm = cv2.normalize(screen_img, None, 0, 255, cv2.NORM_MINMAX)
        # 再用 Gamma=1.5 压暗中间调，杀死噪点
        screen_processed = self.gamma_correction(screen_norm, gamma=1.5)
        
        max_score_found = 0.0
        all_skipped = True 

        for tmpl in template_list:
            tmpl_h, tmpl_w = tmpl.shape[:2]
            
            if screen_h < tmpl_h or screen_w < tmpl_w:
                continue 
            all_skipped = False 

            # 准备模板
            mask = None
            if tmpl.shape[2] == 4:
                tmpl_bgr = cv2.cvtColor(tmpl, cv2.COLOR_BGRA2BGR)
                mask = tmpl[:, :, 3]
            else:
                tmpl_bgr = tmpl
            
            # 模板也做同样的处理：归一化 + Gamma
            tmpl_norm = cv2.normalize(tmpl_bgr, None, 0, 255, cv2.NORM_MINMAX)
            tmpl_processed = self.gamma_correction(tmpl_norm, gamma=1.5)

            try:
                if mask is not None:
                    res = cv2.matchTemplate(screen_processed, tmpl_processed, cv2.TM_CCOEFF_NORMED, mask=mask)
                else:
                    res = cv2.matchTemplate(screen_processed, tmpl_processed, cv2.TM_CCOEFF_NORMED)
                
                _, max_val, _, _ = cv2.minMaxLoc(res)
                
                if np.isinf(max_val) or np.isnan(max_val):
                    max_val = 0.0
                
                if max_val > max_score_found:
                    max_score_found = max_val

            except Exception as e:
                continue

        if all_skipped:
            return ("尺寸错误", 0.0) if return_max_val else False

        if return_max_val:
            return (None, max_score_found)
        else:
            return max_score_found >= threshold
