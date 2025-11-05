
from ap_model import APModel
from llm_client import generate_text
from typing import Any

class WorkshopFlow:
    def __init__(self):
        self.ap = APModel()

    def participant_input(self, key: str, value: Any):
        self.ap.set_element('mt', key, value)

    def ai_infer_related(self, prompt: str, target_timeframe: str = 'mt', field_key: str = 'ai_infer'):
        raw = generate_text(prompt, max_tokens=400)
        self.ap.set_element(target_timeframe, field_key, raw)
        return raw

    def generate_story_process(self):
        "Multi-stage story generation similar to SF-Generator:"
        "1) Create a setting summary based on Mt"
        "2) Expand with Mt-1 and Mt+1 to create richer world"
        "3) Generate full short story"
        "Results saved into ap_model fields: 'setting_summary', 'world_expansion', 'sf_story'."
        mt_text = str(self.ap.mt)
        prompt1 = f"基于以下当前世界（Mt）要素，写一个清晰的设定摘要（300字左右），包含主要冲突与角色雏形：\\n\\n{mt_text}"
        setting = generate_text(prompt1, max_tokens=600)
        self.ap.set_element('mt', 'setting_summary', setting)

        m1_text = str(self.ap.mt_minus1)
        p1_text = str(self.ap.mt_plus1)
        prompt2 = (
            "请基于已生成的设定摘要和历史（Mt-1）与未来（Mt+1）信息，补充世界细节、历史根源、重要事件与技术演进路径，形成可用于小说叙事的世界扩展（500字左右）：\\n\\n"
            f"Setting:\\n{setting}\\n\\nMt-1:\\n{m1_text}\\n\\nMt+1:\\n{p1_text}"
        )
        world_expansion = generate_text(prompt2, max_tokens=800)
        self.ap.set_element('mt', 'world_expansion', world_expansion)

        prompt3 = (
            "请根据以下世界设定（含扩展）写一篇800-1200字的科幻短篇小说，注意人物刻画与冲突弧：\\n\\n"
            f"Setting Summary:\\n{setting}\\n\\nWorld Expansion:\\n{world_expansion}\\n\\nCurrent Mt Data:\\n{mt_text}\\n\\n"
            "请输出完整故事，仅输出故事正文。"
        )
        story = generate_text(prompt3, max_tokens=1200)
        self.ap.set_element('mt', 'sf_story', story)
        return {'setting': setting, 'expansion': world_expansion, 'story': story}
