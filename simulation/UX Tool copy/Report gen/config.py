import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일이 있으면 로드 (선택 사항)
load_dotenv()


GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# 기본 Vision 지원 모델 (필요에 따라 변경 가능)
GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro")


def validate_config() -> None:
    """환경 설정 검증: API 키가 없으면 예외 발생."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.\n"
            "예: export GEMINI_API_KEY='YOUR_API_KEY_HERE'"
        )


