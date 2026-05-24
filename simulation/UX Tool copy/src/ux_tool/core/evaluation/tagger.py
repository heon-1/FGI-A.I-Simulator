from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List


def naive_tags(lines: List[str], top_k: int = 8) -> List[str]:
    text = " ".join(lines).lower()
    tokens = re.findall(r"[a-zA-Z가-힣0-9]{2,}", text)
    stop = {"the", "and", "that", "with", "this", "have", "are", "when", "you"}
    counter = Counter(t for t in tokens if t not in stop)
    return [w for w, _ in counter.most_common(top_k)]


def tag_transcript(lines: List[str]) -> Dict[str, List[str]]:
    return {
        "keywords": naive_tags(lines, top_k=10),
    }


