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
                    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        # 统一转为 BGRA (4通道) 方便后续处理
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
                # 保持 BGRA，保留截图的完整性
                img_bgra = img
                
                h, w = img_bgra.shape[:2]
                self.last_screenshot_shape = f"{w}x{h}"
                
                if debug_name:
                    # 调试保存时转 BGR，因为 imwrite 保存 png alpha 有时会有兼容问题
                    cv2.imwrite(os.path.join(self.debug_dir, f"debug_{debug_name}.png"), cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR))
                
                return img_bgra # 返回 4通道 BGRA
                
        except Exception as e:
            self.last_error = f"截图失败: {str(e)}"
            return None

    def match_templates(self, screen_img, template_list, threshold, return_max_val=False):
        if screen_img is None:
            err = self.last_error if self.last_error else "未获取到截图"
            return (err, 0.0) if return_max_val else False
            
        if not template_list:
            return ("无模板", 0.0) if return_max_val else False

        screen_h, screen_w = screen_img.shape[:2]
        
        # === 预处理 1: 准备普通 BGR 截图 (用于颜色匹配) ===
        screen_bgr = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)
        
        # === 预处理 2: 准备归一化截图 (用于形状匹配) ===
        # 归一化能拉伸对比度，让亮背景下的白色符号显形
        try:
            screen_norm = cv2.normalize(screen_bgr, None, 0, 255, cv2.NORM_MINMAX)
        except:
            screen_norm = screen_bgr

        max_score_found = 0.0
        all_skipped = True 

        for tmpl in template_list:
            tmpl_h, tmpl_w = tmpl.shape[:2]
            
            if screen_h < tmpl_h or screen_w < tmpl_w:
                continue 
            all_skipped = False 

            # 分离通道：BGR 和 Alpha
            tmpl_bgr = tmpl[:, :, :3]
            mask = tmpl[:, :, 3]

            # --- 算法 A: 严格颜色匹配 (SQDIFF) ---
            # 解决红绿区分问题
            score_a = 0.0
            try:
                res_a = cv2.matchTemplate(screen_bgr, tmpl_bgr, cv2.TM_SQDIFF, mask=mask)
                min_val, _, _, _ = cv2.minMaxLoc(res_a)
                valid_pixels = cv2.countNonZero(mask)
                
                if valid_pixels > 0:
                    avg_diff = min_val / valid_pixels
                    # 容忍度 60
                    if avg_diff < 60:
                        score_a = 1.0 - (avg_diff / 60.0)
            except: pass

            # --- 算法 B: 归一化形状匹配 (CCOEFF_NORMED) ---
            # 解决亮背景看不清符号问题
            score_b = 0.0
            try:
                # 仅对模板的颜色部分归一化，不要碰 mask
                tmpl_norm = cv2.normalize(tmpl_bgr, None, 0, 255, cv2.NORM_MINMAX)
                
                res_b = cv2.matchTemplate(screen_norm, tmpl_norm, cv2.TM_CCOEFF_NORMED, mask=mask)
                _, max_val_b, _, _ = cv2.minMaxLoc(res_b)
                score_b = max_val_b
            except: pass

            # === 决策逻辑 ===
            # 1. 如果颜色匹配度极高 (>0.8)，直接采纳。这说明颜色和形状都对上了。
            if score_a > 0.8:
                final_score = score_a
            
            # 2. 如果颜色匹配度低 (可能是背景光干扰，也可能是绿名)
            else:
                # 我们检查形状分 (B)。
                # 如果形状分极高 (>0.92)，我们认为这很可能是“亮背景下的白色符号”，
                # 或者是“受到严重光照干扰的红名”。
                # 为了防止把绿名(形状一样)误判进来，我们必须非常谨慎。
                # 通常绿名和红名的形状分是一样的(都是1.0)，唯一的区别是颜色。
                # 所以：如果颜色分(A)是 0，形状分(B)再高也不能信！
                
                # 但是！对于白色符号，颜色分(A)可能因为背景亮而变低。
                # 这是一个两难。
                
                # 折中方案：
                # 如果是 SQDIFF 算出完全不匹配 (score_a < 0.1)，那肯定是颜色不对(绿名)，直接杀掉。
                # 如果 SQDIFF 算出有一点点像 (score_a > 0.1)，可能是光照干扰，这时才允许用 B 补救。
                
                if score_a < 0.05:
                    final_score = 0.0 # 颜色完全不对，一票否决 (杀绿名)
                else:
                    final_score = score_b # 颜色稍微有点沾边，信赖形状 (救白符号)

            if final_score > max_score_found:
                max_score_found = final_score

        if all_skipped:
            return ("尺寸错误", 0.0) if return_max_val else False

        if return_max_val:
            return (None, max_score_found)
        else:
            return max_score_found >= threshold
