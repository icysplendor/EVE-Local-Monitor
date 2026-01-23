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
                
                if debug_name:
                    cv2.imwrite(os.path.join(self.debug_dir, f"debug_{debug_name}.png"), img_bgr)
                return img_bgr
                
        except Exception as e:
            self.last_error = f"截图失败: {str(e)}"
            return None

    def match_templates(self, screen_img, template_list, threshold, return_max_val=False):
        """
        融合算法：
        1. 严格颜色匹配 (SQDIFF): 解决红绿区分问题。
        2. 归一化形状匹配 (Normalized CCOEFF): 解决亮背景下白色符号看不清的问题。
        """
        if screen_img is None:
            err = self.last_error if self.last_error else "未获取到截图"
            return (err, 0.0) if return_max_val else False
            
        if not template_list:
            return ("无模板", 0.0) if return_max_val else False

        screen_h, screen_w = screen_img.shape[:2]
        
        # === 预处理：归一化 (借鉴你上传的代码) ===
        # 这能极大增强低对比度下的识别能力
        try:
            screen_norm = cv2.normalize(screen_img, None, 0, 255, cv2.NORM_MINMAX)
        except:
            screen_norm = screen_img

        max_score_found = 0.0
        all_skipped = True 

        for tmpl in template_list:
            tmpl_h, tmpl_w = tmpl.shape[:2]
            
            if screen_h < tmpl_h or screen_w < tmpl_w:
                continue 
            all_skipped = False 

            # 准备数据
            if tmpl.shape[2] == 4:
                tmpl_bgr = tmpl[:, :, :3]
                mask = tmpl[:, :, 3]
            else:
                tmpl_bgr = tmpl
                mask = np.ones((tmpl_h, tmpl_w), dtype=np.uint8) * 255

            # --- 算法 A: 严格颜色匹配 (针对红名/本地栏) ---
            # 这是我们之前的算法，对颜色极其敏感，绝不误报绿名
            score_a = 0.0
            try:
                res_a = cv2.matchTemplate(screen_img, tmpl_bgr, cv2.TM_SQDIFF, mask=mask)
                min_val, _, _, _ = cv2.minMaxLoc(res_a)
                valid_pixels = cv2.countNonZero(mask)
                if valid_pixels > 0:
                    avg_diff = min_val / valid_pixels
                    # 容忍度设为 60
                    if avg_diff < 60:
                        score_a = 1.0 - (avg_diff / 60.0)
            except: pass

            # --- 算法 B: 归一化形状匹配 (针对怪物/白色符号) ---
            # 借鉴了你上传代码的思路，但加上了 Mask 支持
            score_b = 0.0
            try:
                # 对模板也进行归一化
                tmpl_norm = cv2.normalize(tmpl_bgr, None, 0, 255, cv2.NORM_MINMAX)
                
                # 使用 CCOEFF_NORMED，它只看形状，不看亮度绝对值
                # 配合 normalize 和 mask，能穿透亮背景识别白色符号
                res_b = cv2.matchTemplate(screen_norm, tmpl_norm, cv2.TM_CCOEFF_NORMED, mask=mask)
                _, max_val_b, _, _ = cv2.minMaxLoc(res_b)
                
                # 只有当分数非常高时才采纳，防止形状误报
                # 因为这个算法不看颜色，容易把绿名当红名，所以我们只用它来“兜底”那些特别难识别的高亮符号
                if max_val_b > 0.8: 
                    score_b = max_val_b
            except: pass

            # === 智能融合决策 ===
            # 如果是红名检测（本地/总览），我们主要信赖 A
            # 如果是白色符号（怪物），A 可能会低，B 会很高
            
            # 这里取巧：如果 A 很高（颜色对上了），直接用 A
            if score_a > 0.6:
                final_score = score_a
            else:
                # 如果颜色没对上（可能是背景光干扰，也可能是真的不匹配）
                # 我们看 B (形状)。如果形状分极高 (>0.9)，我们认为可能是光照问题，给予通过
                # 但为了防止绿名误报，我们对 B 进行打折
                if score_b > 0.9:
                    final_score = score_b * 0.95 # 稍微扣点分表示不确定
                else:
                    final_score = score_b * 0.8 # 形状一般，颜色不对 -> 低分

            if final_score > max_score_found:
                max_score_found = final_score

        if all_skipped:
            return ("尺寸错误", 0.0) if return_max_val else False

        if return_max_val:
            return (None, max_score_found)
        else:
            return max_score_found >= threshold
