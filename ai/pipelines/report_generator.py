import os
import json
from google import genai

class MonthylyReportGenerator:
    def __init__(self, api_key: str, prompt_path: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-3-flash-preview"
        self.prompt_path = prompt_path

    def _load_prompt_template(self):
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompt_path}")
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _clean_keys(self, data):
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                clean_key = (str(k)
                            .strip()
                            .replace('\n', '')
                            .replace('\r', '')
                            .replace('"', '')
                            .replace("'", '')
                            .replace(' ', ''))
                cleaned[clean_key] = self._clean_keys(v)
            return cleaned
        return data

    async def generate_report(self, variables: dict):
        template = self._load_prompt_template()
        final_prompt = template.format(**variables)

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=final_prompt,
            config={'response_mime_type': 'application/json'}
        )

        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
        raw_text = raw_text.strip("`")

        try:
            parsed_json = json.loads(raw_text)
            return self._clean_keys(parsed_json)
        except json.JSONDecodeError:
            print(f"JSON 파싱 실패! 원본 데이터:\n{response.text}")
            raise
        except Exception as e:
            print(f"[DEBUG] generate_report 에러 타입: {type(e)}\n\n")
            print(f"[DEBUG] generate_report 에러 내용: {e}\n\n")
            print(f"[DEBUG] raw_text 내용:\n{raw_text}")
            raise
