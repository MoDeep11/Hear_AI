from ai.pipelines.feedback_generator import FeedbackGenerator

class FeedbackService:
    def __init__(self):
        self.generator = FeedbackGenerator()

    async def get_diary_feedback(self, data):
        # 파이프라인 호출
        ai_comment = self.generator.generate(
            nickname=data.nickname,
            content=data.content,
            emotion=data.emotion
        )
        return ai_comment