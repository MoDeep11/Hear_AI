from ai.pipelines.chat_init import ChatGenerator
from typing import Dict

async def initialize_session(data: Dict):
    """
    세션 ID와 유저 정보를 받아 AI 첫 인사를 생성합니다.
    """
    session_id = data.get("sessionId")
    user_info = data.get("userInfo")

    # AI 파이프라인 호출
    initial_message = await ChatGenerator.generate_initial_greeting(user_info)

    return {
        "sessionId": session_id,
        "initialMessage": initial_message
    }