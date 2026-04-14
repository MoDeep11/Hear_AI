import asyncio
from ai.pipelines.feedback_generator import FeedbackGenerator

class FeedbackService:
    def __init__(self):
        self.generator = FeedbackGenerator()

    async def get_diary_feedback(self, data):
        def generate_sync():
            nickname = data.get("nickname") if isinstance(data, dict) else getattr(data, "nickname", "")
            content = data.get("content") if isinstance(data, dict) else getattr(data, "content", "")
            emotion = data.get("emotion") if isinstance(data, dict) else getattr(data, "emotion", "")
            return self.generator.generate(
                nickname=nickname,
                content=content,
                emotion=emotion
            )

        return await asyncio.to_thread(generate_sync)
