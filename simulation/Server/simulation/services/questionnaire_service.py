"""
Questionnaire Generation Service
Generate FGI and Individual interview questionnaires using AI
"""
from typing import List, Optional
import orjson
from simulation.types import Questionnaire, Question
from simulation.services.gemini_client import get_gemini_client


class QuestionnaireService:
    """
    Service for generating and managing questionnaires.
    Supports both FGI and Individual interview formats.
    """

    def __init__(self):
        self.client = get_gemini_client()

    def generate_fgi_questionnaire(
        self,
        topic: str,
        objective: str,
        target_audience: str,
        question_count: int = 8,
        additional_context: Optional[str] = None
    ) -> Questionnaire:
        """
        Generate FGI questionnaire based on research topic.
        
        Args:
            topic: Research topic/theme
            objective: Research objective
            target_audience: Target audience description
            question_count: Number of questions to generate
            additional_context: Additional context or constraints
            
        Returns:
            Generated questionnaire
        """
        prompt = self._build_fgi_prompt(
            topic, objective, target_audience, 
            question_count, additional_context
        )
        response = self.client.generate(prompt)
        return self._parse_questionnaire_response(response, f"fgi_{topic[:20]}")

    def generate_individual_questionnaire(
        self,
        topic: str,
        objective: str,
        target_audience: str,
        question_count: int = 10,
        include_scale_questions: bool = True,
        include_multi_questions: bool = True,
        additional_context: Optional[str] = None
    ) -> Questionnaire:
        """
        Generate Individual interview questionnaire.
        
        Args:
            topic: Research topic
            objective: Research objective
            target_audience: Target audience
            question_count: Number of questions
            include_scale_questions: Include 1-7 scale questions
            include_multi_questions: Include multiple choice questions
            additional_context: Additional constraints
            
        Returns:
            Generated questionnaire
        """
        prompt = self._build_individual_prompt(
            topic, objective, target_audience, question_count,
            include_scale_questions, include_multi_questions, additional_context
        )
        response = self.client.generate(prompt)
        return self._parse_questionnaire_response(response, f"ind_{topic[:20]}")

    def _build_fgi_prompt(
        self,
        topic: str,
        objective: str,
        target_audience: str,
        question_count: int,
        additional_context: Optional[str]
    ) -> str:
        """Build prompt for FGI questionnaire generation"""
        context_text = f"\n추가 맥락: {additional_context}" if additional_context else ""
        
        return f"""당신은 전문 UX 리서처입니다. 다음 주제에 대한 FGI(Focus Group Interview) 설문지를 생성해주세요.

주제: {topic}
연구 목적: {objective}
대상: {target_audience}
질문 수: {question_count}개{context_text}

FGI 설문지 설계 원칙:
1. 워밍업 질문으로 시작 (참가자들이 편하게 시작할 수 있도록)
2. 주제에 대한 일반적 경험 → 구체적 사례 → 평가/개선점 순서로 진행
3. 개방형 질문 위주 (참가자 간 토론 유도)
4. 1-7점 척도 질문 1-2개 포함 (정량적 파악)
5. 마무리 질문으로 종결 (추가 의견, 요약)

각 질문은 다음 필드를 포함해야 합니다:
- id: 고유 ID (q1, q2, ...)
- text: 질문 내용 (구체적이고 명확하게)
- kind: 질문 유형 ("open", "scale", "multi" 중 하나)
- scale_min, scale_max: kind가 "scale"일 때만 (예: 1, 7)
- options: kind가 "multi"일 때만 (선택지 배열)

JSON 형식으로 다음 구조를 따라 출력해주세요:
{{
  "id": "questionnaire_id",
  "title": "설문 제목",
  "instructions": "모더레이터를 위한 진행 가이드",
  "questions": [
    {{"id": "q1", "text": "질문 내용", "kind": "open"}},
    {{"id": "q2", "text": "질문 내용", "kind": "scale", "scale_min": 1, "scale_max": 7}},
    ...
  ]
}}

JSON만 출력하세요. 설명이나 코드블록 마크다운 없이."""

    def _build_individual_prompt(
        self,
        topic: str,
        objective: str,
        target_audience: str,
        question_count: int,
        include_scale: bool,
        include_multi: bool,
        additional_context: Optional[str]
    ) -> str:
        """Build prompt for Individual questionnaire generation"""
        context_text = f"\n추가 맥락: {additional_context}" if additional_context else ""
        
        question_types = ["개방형 질문"]
        if include_scale:
            question_types.append("1-7점 척도 질문 (2-3개)")
        if include_multi:
            question_types.append("객관식 질문 (1-2개)")
        
        return f"""당신은 전문 UX 리서처입니다. 다음 주제에 대한 1:1 심층 인터뷰 설문지를 생성해주세요.

주제: {topic}
연구 목적: {objective}
대상: {target_audience}
질문 수: {question_count}개
질문 유형: {', '.join(question_types)}{context_text}

1:1 인터뷰 설문지 설계 원칙:
1. 라포 형성을 위한 가벼운 도입 질문
2. 경험 탐색 → 동기/니즈 파악 → 페인포인트 발견 순서
3. 프로빙 가능한 개방형 질문 위주
4. 정량적 파악을 위한 척도 질문 포함
5. 미래 니즈/기대사항 질문
6. 자유 의견 마무리

각 질문은 다음 필드를 포함해야 합니다:
- id: 고유 ID (q1, q2, ...)
- text: 질문 내용 (심층적이고 구체적으로)
- kind: 질문 유형 ("open", "scale", "multi" 중 하나)
- scale_min, scale_max: kind가 "scale"일 때만 (예: 1, 7)
- options: kind가 "multi"일 때만 (선택지 배열)

JSON 형식으로 다음 구조를 따라 출력해주세요:
{{
  "id": "questionnaire_id",
  "title": "설문 제목",
  "instructions": "인터뷰어를 위한 진행 가이드",
  "questions": [
    {{"id": "q1", "text": "질문 내용", "kind": "open"}},
    {{"id": "q2", "text": "질문 내용", "kind": "scale", "scale_min": 1, "scale_max": 7}},
    {{"id": "q3", "text": "질문 내용", "kind": "multi", "options": ["옵션1", "옵션2", "옵션3"]}},
    ...
  ]
}}

JSON만 출력하세요. 설명이나 코드블록 마크다운 없이."""

    def _parse_questionnaire_response(self, response: str, fallback_id: str) -> Questionnaire:
        """Parse AI response into Questionnaire object"""
        try:
            data = orjson.loads(response)
        except Exception:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = response[start:end + 1]
                data = orjson.loads(snippet)
            else:
                raise ValueError("Failed to parse questionnaire response")
        
        # Ensure required fields
        if "id" not in data:
            data["id"] = fallback_id
        if "title" not in data:
            data["title"] = "Generated Questionnaire"
        if "questions" not in data:
            raise ValueError("No questions in response")
        
        # Parse questions
        questions = []
        for i, q in enumerate(data["questions"]):
            questions.append(Question(
                id=q.get("id") or f"q{i+1}",
                text=q.get("text") or "",
                kind=q.get("kind") or "open",
                scale_min=q.get("scale_min"),
                scale_max=q.get("scale_max"),
                options=q.get("options") or []
            ))
        
        return Questionnaire(
            id=data["id"],
            title=data["title"],
            instructions=data.get("instructions") or "",
            questions=questions
        )

    def enhance_questionnaire(
        self,
        questionnaire: Questionnaire,
        feedback: str
    ) -> Questionnaire:
        """
        Enhance existing questionnaire based on feedback.
        
        Args:
            questionnaire: Existing questionnaire to enhance
            feedback: User feedback for improvement
            
        Returns:
            Enhanced questionnaire
        """
        current_questions = "\n".join([
            f"- {q.id}: {q.text} (kind: {q.kind})"
            for q in questionnaire.questions
        ])
        
        prompt = f"""기존 설문지를 피드백을 반영하여 개선해주세요.

현재 설문지:
제목: {questionnaire.title}
안내: {questionnaire.instructions}
질문들:
{current_questions}

피드백: {feedback}

개선된 설문지를 동일한 JSON 형식으로 출력해주세요.
기존 질문을 수정하거나, 새 질문을 추가하거나, 불필요한 질문을 제거할 수 있습니다.

JSON만 출력하세요. 설명이나 코드블록 없이."""

        response = self.client.generate(prompt)
        return self._parse_questionnaire_response(response, questionnaire.id)
