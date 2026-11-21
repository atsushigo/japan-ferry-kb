"""Output guardrail for the Dify chatflow: block answers that contain a money amount the knowledge base does not contain.

Paste the whole file into a Dify "Code" node (language: Python 3), placed between the LLM node and the answer node.
Input variables of the node (names must match):
    answer   <- LLM node, `text`
    context  <- knowledge-retrieval node, `result`
Output variables of the node (declare both as String):
    verdict  "pass" or "block"
    bad      the amounts that were not found in the retrieved text (for the log; "" when pass)

Rule (same as evaluation/score_chat.py, check `numeric_grounding`): every amount written next to a currency mark
(₩ ¥ ￥, or a number followed by 韓元 / 円 / 日圓 / RMB / 人民幣 / 元 ...) in the answer must also appear, as the
same number, next to a currency mark in the retrieved text. Numbers without a currency mark (person counts,
percentages, dates, phone numbers) are not checked. Standard library only.
"""
import json
import re

_NUM = r"\d[\d,]*(?:\.\d+)?"
_SYM = r"[₩¥￥]"
_UNIT = r"(?:韓元|韓圜|원|KRW|JPY|日圓|日元|円|RMB|CNY|人民幣|元)"
_AMOUNT_RES = [re.compile(rf"{_SYM}\s?({_NUM})"), re.compile(rf"({_NUM})\s?{_UNIT}"),
               re.compile(rf"(?:KRW|JPY|RMB|CNY)\s?({_NUM})")]


def _amounts(text):
    found = set()
    for rx in _AMOUNT_RES:
        for m in rx.finditer(text or ""):
            found.add(m.group(1).replace(",", "").rstrip("."))
    return found


def _to_text(x):
    """The retrieval result is a list of objects in Dify; accept a plain string too."""
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(x)


def main(answer, context):
    bad = sorted(a for a in _amounts(_to_text(answer)) if a not in _amounts(_to_text(context)))
    return {"verdict": "block" if bad else "pass", "bad": ",".join(bad)}
