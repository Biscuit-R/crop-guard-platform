"""DeepSeek 云 LLM 客户端（D7）。

薄封装：只做 prompt 组装与错误映射。重试、超时、协议细节交给 openai SDK ——
DeepSeek 是 OpenAI 兼容接口，换供应商只改 base_url 与模型名。
"""

from openai import OpenAI

from app.rag.retriever import Retrieved

SYSTEM_PROMPT = (
    "你是作物虫害防治助手。你只能依据用户提供的图鉴资料回答问题，"
    "不得使用资料之外的知识；回答末尾用【来源：中文名】标注所依据的条目；"
    "如果资料不足以回答，明确说明资料中没有相关内容，不要猜测。"
)


def build_messages(query: str, hits: list[Retrieved], history: list[dict] | None = None) -> list[dict]:
    """把检索块编成编号资料 + 用户问题。编号是溯源的最小实现。

    history 是会话记忆里的最近几轮（{q, a}），按原顺序插在 system 之后，
    让「那叶子发黄呢？」这类指代性问题能借上下文理解。
    """
    context = "\n\n".join(f"【资料{i}】{h.content}" for i, h in enumerate(hits, 1))
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        messages.append({"role": "user", "content": turn["q"]})
        messages.append({"role": "assistant", "content": turn["a"]})
    messages.append({"role": "user", "content": f"图鉴资料：\n{context}\n\n用户问题：{query}"})
    return messages


class LLMError(Exception):
    """LLM 不可用（网络/鉴权/限流）。上层据此走 fail-open 降级。"""


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat", timeout: float = 30.0):
        self._model = model
        # timeout 必须显式给：SDK 默认 600s，挂住的 LLM 会拖死请求而非降级
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def generate(self, query: str, hits: list[Retrieved], history: list[dict] | None = None) -> str:
        return self.chat_raw(build_messages(query, hits, history))

    def chat_raw(self, messages: list[dict]) -> str:
        """最低层调用：消息进、文本出。追问澄清等非检索场景也走这里。"""
        try:
            resp = self._client.chat.completions.create(model=self._model, messages=messages)
        except Exception as e:
            raise LLMError(f"LLM 调用失败：{e}") from e
        return resp.choices[0].message.content

    def __call__(self, query: str, hits: list[Retrieved], history: list[dict] | None = None) -> str:
        """让客户端实例可直接作为 answer() 的 llm 参数——
        qa 层除了要会作答（__call__）还要会澄清（chat_raw），传实例而不是方法。"""
        return self.generate(query, hits, history)
