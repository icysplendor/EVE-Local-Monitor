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
    "thresholds": {
        "local": 0.95,    # [修改] 明确区分 local
        "overview": 0.95, # [新增] 明确区分 overview
        "monster": 0.95   # [修改] 默认值改为 0.95
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
                    # 深度合并逻辑，防止新加的字段在旧配置里不存在而报错
                    for k, v in data.items():
                        if k in self.config:
                            if isinstance(v, dict):
                                for sub_k, sub_v in v.items():
                                    if sub_k in self.config[k]:
                                        self.config[k][sub_k] = sub_v
                                    else:
                                        # 如果旧配置里没有这个子字段，保留默认值
                                        pass
                            else:
                                self.config[k] = v
            except:
                print("Config load failed, using defaults.")

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value
        self.save()
