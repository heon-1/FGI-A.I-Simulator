## IR PDF 기반 Gemini 터미널 Q&A 도구

IR(투자설명서, 사업보고서 등) PDF를 **Google Gemini**(Vision 지원)로 분석한 뒤,  
터미널에서 한국어로 질의응답을 할 수 있는 간단한 예제입니다.

### 1. 준비물

- **Python 3.9+**
- **Google AI Studio / Google Cloud** 에서 발급한 Gemini API 키  
  - 환경변수 `GEMINI_API_KEY` 로 설정합니다.

```bash
export GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

### 2. 라이브러리 설치

프로젝트 루트(`/Users/admin/Desktop/Product/Repport gen`)에서:

```bash
cd "/Users/admin/Desktop/Product/Repport gen"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 사용 방법

IR PDF 파일을 예시로 `./samples/ir.pdf` 라고 할 때:

```bash
python ir_qa.py --pdf "1114.pdf"
```

실행하면 PDF를 업로드한 뒤, 아래와 같은 형식으로 질의응답을 진행할 수 있습니다.

- `q` 입력: 질문 (예: *"올해 매출과 영업이익 요약해줘"*)
- `exit` / `quit`: 프로그램 종료

### 4. 파일 설명

- `ir_qa.py`  
  - 메인 진입점.  
  - IR PDF를 Gemini에 업로드하고, 터미널 인터랙티브 Q&A 루프를 관리합니다.
- `config.py`  
  - `GEMINI_API_KEY`, 사용할 모델 이름 등을 환경변수에서 읽어옵니다.

### 5. 참고

- 기본 모델은 `gemini-1.5-flash` 로 설정되어 있습니다.  
  보다 정교한 분석이 필요하면 `config.py` 에서 `GEMINI_MODEL_NAME` 을 `gemini-1.5-pro` 등으로 변경할 수 있습니다.


