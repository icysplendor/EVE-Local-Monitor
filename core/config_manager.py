import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "language": "CN",
    "regions": {
        "local": None,
        "overview": None,
        "monster": None
    },
    # 修改：拆分阈值，且默认值改为 0.95
    "thresholds": {
        "local": 0.95,
        "overview": 0.95,
        "monster": 0.95
    },
    "webhook_url": "",
    "audio_paths": {
        "local": "",
        "overview": "",
        "monster": "",
        "mixed": ""
    }
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 深度合并逻辑，确保新增加的字段（如拆分后的阈值）能从默认配置中生效
                    for k, v in data.items():
                        if k in self.config:
                            if isinstance(v, dict):
                                # 如果是字典，进行增量更新，防止旧配置覆盖新结构
                                for sub_k, sub_v in v.items():
                                    if sub_k in self.config[k]:
                                        self.config[k][sub_k] = sub_v
                            else:
                                self.config[k] = v
            except:
                print("加载配置文件失败，使用默认配置")

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value
        self.save()
