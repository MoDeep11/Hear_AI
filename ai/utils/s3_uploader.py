import boto3
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class S3Uploader:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
        )
        self.bucket_name = os.getenv("AWS_BUCKET_NAME", "hear-official")

    async def upload_file(self, local_path: str, s3_key: str) -> str:
        """파일을 S3에 업로드하고 URL을 반환합니다."""
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                self.s3_client.upload_file,
                local_path,
                self.bucket_name,
                s3_key,
            )
            # return f"https://{self.bucket_name}.s3.ap-northeast-2.amazonaws.com/{s3_key}"
            return f"실패"
        except Exception as e:
            print(f"S3 업로드 에러: {e}")
            return ""

s3_uploader = S3Uploader()