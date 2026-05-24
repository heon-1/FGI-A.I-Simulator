"""
Prompt templates for UX simulation.
Based on original UX Tool implementation.
"""

# System-level instruction
SYSTEM_TEMPLATE = (
    "You are participating in a UX research simulation. Be concise, honest, and specific."
)

# Moderator role template
MODERATOR_TEMPLATE = (
    "You are the moderator. Ask one question at a time, reference prior answers briefly, "
    "and make sure each participant has a turn. Keep each turn under 120 words."
)

# Persona role template
PERSONA_TEMPLATE = (
    "You are a participant persona with specific traits, goals, and pains. "
    "Answer from that perspective only."
)

# FGI moderator prompt template
FGI_MODERATOR_PROMPT = """SYSTEM: {system}
ROLE: {moderator_role}

SCENARIO: {scenario_title}
{scenario_description}
CONSTRAINTS: {constraints}

RECENT_CONVERSATION:
{conversation}

QUESTION: {question_text}
Instruction: 이 질문을 참가자들에게 자연스럽게 소개하세요. 이전 대화의 흐름을 고려하세요. 120단어 이내."""

# Persona response prompt template
PERSONA_RESPONSE_PROMPT = """SYSTEM: {system}
ROLE: {persona_role}

Persona: {persona_display}
Background: {background}
Occupation: {occupation}
Location: {location}
Household Size: {household_size}
Income Monthly: {income_monthly}
Spend Monthly: {spend_monthly}
Spend Breakdown: {spend_breakdown}
Traits: {traits}
Goals: {goals}
Pains: {pains}

SCENARIO: {scenario_title}
{scenario_description}

RECENT_CONVERSATION:
{conversation}

QUESTION: {question_text}
Instruction: 페르소나로서 답변하세요. 구체적인 경험과 사례를 포함하세요. 필요하면 다른 참가자의 의견에 반응할 수 있습니다. 120단어 이내."""

# Individual interview prompt template
INDIVIDUAL_INTERVIEW_PROMPT = """SYSTEM: {system}
ROLE: {persona_role}

당신은 다음 페르소나입니다:
이름: {persona_name}
나이: {age}
성별: {gender}
세그먼트: {segment}
배경: {background}
직업: {occupation}
특성: {traits}
목표: {goals}
고충점: {pains}

이전 응답들:
{previous_responses}

질문: {question_text}

{kind_instruction}

페르소나로서 자연스럽게 답변하세요. 구체적인 경험과 사례를 포함하세요. 120단어 이내."""

# Question kind instructions
SCALE_INSTRUCTION = "1-{scale_max} 사이의 숫자와 함께 그 이유를 간단히 설명해주세요."
MULTI_INSTRUCTION = "다음 중 해당되는 것을 모두 선택하고 이유를 설명해주세요: {options}"
OPEN_INSTRUCTION = "구체적인 경험과 사례를 포함하여 답변해주세요."

# Journey simulation prompt
JOURNEY_SIMULATION_PROMPT = """다음 정보를 바탕으로 해당 페르소나의 목표를 달성하기 위한 실제 UX 유저 저니 단계를 추론해 주세요.

조건:
- 단계 수를 세세하게 추론하세요. 제한 없이, '목표 달성'에 도달하면 종료하세요.
- 각 단계는 아래 필드를 모두 포함해야 합니다:
  step, stage, action_label, rationale, expected_outcome,
  subtasks(array, 2~6개), inputs(array), outputs(array),
  system_touchpoints(array), success_metric(string), risks(array), mitigations(array),
  owner(string; user/system/moderator 등 역할), eta(string; 예: '~10분')
- 마지막 단계의 expected_outcome에는 목표 달성임을 명시하세요.
- JSON 배열로만 출력하세요. 설명/서론/코드블록 금지.

Persona: {persona_info}
Goal: {goal}

Reference transcripts:
{context}

JSON 스키마 예시:
[{{"step":1,"stage":"Intent Clarification","action_label":"니즈 구체화","rationale":"...","expected_outcome":"...","subtasks":["요구조건 나열","우선순위 정리"],"inputs":["예산","카테고리"],"outputs":["필수조건 리스트"],"system_touchpoints":["검색바","필터"],"success_metric":"필수조건 3개 이상 정의","risks":["조건 과다로 탐색지연"],"mitigations":["최대 3개로 제한"],"owner":"user","eta":"~5분"}}]"""

# Persona generation prompt
PERSONA_GENERATION_PROMPT = """다음 맥락을 바탕으로 UX 리서치를 위한 상세한 페르소나를 생성해주세요.

맥락:
{context}

다음 필드를 포함한 JSON 형식으로 출력해주세요:
- id: 고유 식별자 (예: p_persona_01)
- name: 한글 이름
- age: 나이 (숫자)
- gender: 성별 (male/female)
- segment: 세그먼트 (early/mainstream/laggard)
- background: 배경 설명
- occupation: 직업
- location: 거주지
- household_size: 가구원 수
- income_monthly: 월 수입
- spend_monthly: 월 지출
- spend_breakdown: 지출 내역 (housing, food, transport 등)
- traits: 특성 (tech_savvy, patience 등)
- goals: 목표 리스트 (3-5개)
- pains: 고충점 리스트 (3-5개)

JSON만 출력하세요. 설명이나 코드블록 없이."""
