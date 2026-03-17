# from google import genai
# import json
# import os

# class DiaryGenerator:
#     def __init__(self, api_key: str):
#         # 최신 SDK에서는 Client 객체를 하나 생성하여 관리
#         self.client = genai.Client(api_key=api_key)
#         self.model_id = 'models/gemini-2.5-flash'
#         self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diary_generation.txt")

#     async def generate_response(self, user_text, history, user_info):
#         # txt 파일 읽기
#         if not os.path.exists(self.prompt_path):
#             raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompt_path}")
            
#         with open(self.prompt_path, "r", encoding="utf-8") as f:
#             template = f.read()
        
#         prompt = template.format(
#             user_info=json.dumps(user_info, ensure_ascii=False),
#             history=json.dumps(history, ensure_ascii=False),
#             user_text=user_text,
#             diary_content_or_question=user_text,
#             session_id=user_info.get("sessionId", "unknown")
#         )
        
#         response = self.client.models.generate_content(
#             model=self.model_id,
#             contents=prompt
#         )
        
#         # JSON 파싱
#         content = response.text.strip()
        
#         # 마크다운 코드 블록 제거 로직
#         if content.startswith("```"):
#             lines = content.splitlines()
#             # 첫 줄(```json)과 마지막 줄(```)을 제외한 나머지 합치기
#             content = "\n".join(lines[1:-1]) if lines[0].startswith("```") else content
        
#         try:
#             return json.loads(content)
#         except json.JSONDecodeError:
#             # 혹시나 JSON 형식이 아닐 경우를 대비한 예외 처리
#             print(f"JSON 파싱 에러 발생. 원문: {content}")
#             return {"status": "CONTINUE", "aiResponseText": "죄송해요, 다시 한번 말씀해 주시겠어요?", "suggestion": None}


from google import genai
import json
import os
import asyncio

class DiaryGenerator:
    def __init__(self, api_key: str):
        # 최신 SDK Client 객체 생성
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'models/gemini-2.5-flash' 
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diary_generation.txt")

    async def generate_response(self, user_text, history, user_info):
        """
        Gemini API를 호출하여 유저의 입력에 대한 응답을 생성합니다.
        """
        # 1. 프롬프트 템플릿 읽기
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompt_path}")
            
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        # 2. 템플릿 변수 치환
        # 유저 정보와 대화 기록을 JSON 문자열로 변환하여 프롬프트에 주입
        current_sid = user_info.get("sessionId") or user_info.get("session_id") or "unknown"
        prompt = template.format(
            user_info=json.dumps(user_info, ensure_ascii=False),
            history=json.dumps(history, ensure_ascii=False),
            user_text=user_text,
            diary_content_or_question=user_text,
            session_id=current_sid  
        )
        
        try:
            # 3. Gemini API 호출 (비동기 처리를 위해 run_in_executor 또는 SDK의 비동기 지원 확인)
            # 현재 google-genai SDK는 동기 호출이 기본이므로, loop를 사용해 비동기처럼 작동하게 합니다.
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt
                )
            )
            
            # 4. 결과 텍스트 추출 및 마크다운 정리
            content = response.text.strip()
            
            # 마크다운 코드 블록(```json ... ```) 제거
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    # 첫 줄과 마지막 줄 제외
                    content = "\n".join(lines[1:-1])

            # 5. JSON 파싱
            return json.loads(content)

        except json.JSONDecodeError as je:
            print(f"JSON 파싱 에러: {str(je)} | 원문: {content}")
            return {
                "status": "CONTINUE", 
                "aiResponseText": "음, 방금 말씀하신 내용을 제가 잘 이해하지 못했어요. 다시 한 번 이야기해 주실래요?", 
                "suggestion": None
            }
        except Exception as e:
            print(f"Gemini API 호출 에러: {str(e)}")
            return {
                "status": "CONTINUE", 
                "aiResponseText": "잠시 통신이 원활하지 않아요. 다시 시도해 주세요!", 
                "suggestion": None
            }