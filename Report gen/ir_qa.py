import argparse
import sys
import time
from typing import Optional

import google.generativeai as genai
from rich.console import Console
from rich.prompt import Prompt

from config import GEMINI_API_KEY, GEMINI_MODEL_NAME, validate_config


console = Console()


def init_gemini() -> genai.GenerativeModel:
    """Gemini 클라이언트 초기화."""
    validate_config()
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    return model


def upload_pdf(model: genai.GenerativeModel, pdf_path: str):
    """PDF 파일을 Gemini File API로 업로드."""
    console.print(f"[bold cyan]PDF 업로드 중...[/bold cyan] [dim]({pdf_path})[/dim]")
    file = genai.upload_file(pdf_path)

    # 업로드 처리 상태가 완료될 때까지 대기
    while file.state.name == "PROCESSING":
        time.sleep(1)
        file = genai.get_file(file.name)

    if file.state.name != "ACTIVE":
        raise RuntimeError(f"파일 처리 실패: {file.state.name}")

    console.print(
        f"[green]업로드 완료[/green] (name: [dim]{file.name}[/dim], mime: {file.mime_type})"
    )
    return file


def answer_question(
    model: genai.GenerativeModel,
    file,
    question: str,
    system_instruction: Optional[str] = None,
) -> str:
    """PDF를 컨텍스트로 사용하여 질문에 답변."""
    # 시스템 인스트럭션: IR/재무 문서 중심으로 답변하도록 가이드
    base_instruction = (
        "당신은 한국어를 사용하는 재무/IR 분석 보조 도구입니다. "
        "주어진 IR/재무 PDF 내용을 기반으로만 답변하고, "
        "추측은 최소화하며, 모르는 내용은 모른다고 말하세요. "
        "숫자(매출, 영업이익 등)는 표에서 그대로 가져와 요약해 주세요."
        "답변은 마크다운 형식을 사용하지 말고, 일반 텍스트로만 제공하세요."
    )
    if system_instruction:
        base_instruction += "\n추가 지시사항: " + system_instruction

    prompt_parts = [
        base_instruction,
        "\n\n[사용자 질문]\n" + question,
    ]

    # File + 텍스트를 함께 전달
    response = model.generate_content(
        [
            file,
            "\n\n",
            *prompt_parts,
        ],
    )

    return response.text.strip() if response.text else ""


def interactive_loop(model: genai.GenerativeModel, file) -> None:
    """터미널에서 질의응답 루프."""
    console.print(
        "[bold]IR PDF 기반 Gemini Q&A 모드[/bold]\n\n"
        "모드를 선택할 수 있습니다.\n"
        "1) 일반 질의응답 모드: 자유로운 질문/답변\n"
        "2) 보고서 섹션 작성 모드: 예) '창업아이템 목표시장(고객) 현황 분석' 처럼 섹션 제목을 입력하면,\n"
        "   IR 데이터를 근거로 해당 항목에 대한 분석/서술을 보고서 형식으로 생성합니다.\n\n"
        "- 종료하려면 [bold]exit[/bold] 또는 [bold]quit[/bold] 입력."
    )

    mode = Prompt.ask(
        "[bold cyan]모드 선택 (1=일반 Q&A, 2=보고서 섹션 작성)[/bold cyan]",
        choices=["1", "2"],
        default="1",
        show_choices=True,
    )
    report_mode = mode == "2"

    if report_mode:
        console.print(
            "[green]보고서 섹션 작성 모드입니다.[/green] "
            "입력하는 문장은 섹션 제목으로 간주되며, IR 데이터를 기반으로 해당 항목을 분석/서술합니다."
        )
    else:
        console.print("[green]일반 질의응답 모드입니다.[/green]")

    while True:
        try:
            q = Prompt.ask("[bold yellow]질문 입력[/bold yellow]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[red]종료합니다.[/red]")
            break

        if not q:
            continue

        if q.lower() in {"exit", "quit"}:
            console.print("[red]종료합니다.[/red]")
            break

        console.print("[dim]Gemini가 답변 생성 중...[/dim]")
        try:
            system_instruction = None
            if report_mode:
                system_instruction = (
                    "사용자가 입력하는 문장은 보고서의 섹션 제목입니다. "
                    "해당 제목에 맞추어, IR PDF에 포함된 데이터를 최대한 근거로 삼아 "
                    "분석·설명·시사점을 한국어 보고서 형식으로 작성하세요. "
                    "가능하면 소제목과 bullet을 적절히 섞어 구조화하고, "
                    "수치를 언급할 때는 어떤 내용(매출, 고객수, 시장규모 등)에 대한 것인지 명확히 적어주세요. "
                    "근거가 문서에 없으면 추측하지 말고, '문서에 해당 데이터가 명시되어 있지 않습니다'라고 밝혀주세요."
                )

            answer = answer_question(model, file, q, system_instruction=system_instruction)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]오류 발생:[/red] {e}")
            continue

        console.print("\n[bold green]답변:[/bold green]")
        console.print(answer)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="IR PDF 기반 Gemini 터미널 Q&A 도구"
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="분석할 IR PDF 파일 경로",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    try:
        model = init_gemini()
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Gemini 초기화 실패:[/red] {e}")
        return 1

    try:
        file = upload_pdf(model, args.pdf)
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]PDF 업로드/처리 중 오류:[/red] {e}")
        return 1

    interactive_loop(model, file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


