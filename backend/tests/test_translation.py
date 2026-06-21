"""Language detection + English-pivot translation (multilingual intake)."""
from __future__ import annotations

from app.engines import translation as T

EN = "Senior engineer with 10 years building scalable Python backend services and leading teams."
ZH = "拥有十年经验的高级工程师，擅长构建可扩展的后端服务并领导团队。"
JA = "10年の経験を持つシニアエンジニア。スケーラブルなバックエンドの構築とチームの統率。"
TA = "பத்து ஆண்டுகள் அனுபவம் கொண்ட மூத்த பொறியாளர்; அளவிடக்கூடிய பின்தளங்களை உருவாக்குபவர்."
HI = "दस साल के अनुभव वाले वरिष्ठ इंजीनियर; स्केलेबल बैकएंड सेवाओं का निर्माण।"
MS = ("Jurutera kanan dengan sepuluh tahun pengalaman membina perkhidmatan "
      "backend yang berskala dan memimpin pasukan.")


def test_english_is_not_flagged():
    assert T.likely_non_english(EN) is False


def test_non_latin_scripts_flagged():
    for s in (ZH, JA, TA, HI):
        assert T.likely_non_english(s) is True


def test_latin_script_non_english_flagged_by_markers():
    # Malay uses the Latin alphabet but lacks English function words.
    assert T.likely_non_english(MS) is True


def test_short_text_not_flagged():
    assert T.likely_non_english("Hi there") is False
    assert T.likely_non_english("") is False


def test_english_passes_through_untranslated(monkeypatch):
    monkeypatch.setattr(T, "is_live", lambda: True)
    out = T.to_english(EN)
    assert out["source_language"] == "en"
    assert out["method"] == "passthrough"
    assert out["english_text"] == EN


def test_non_english_offline_keeps_original(monkeypatch):
    monkeypatch.setattr(T, "is_live", lambda: False)
    out = T.to_english(ZH)
    assert out["english_text"] == ZH  # never dropped
    assert out["method"] == "passthrough-offline"


def test_non_english_live_translates(monkeypatch):
    monkeypatch.setattr(T, "is_live", lambda: True)
    monkeypatch.setattr(T, "call_claude_json", lambda **k: {
        "source_language": "zh", "confidence": 0.98,
        "english_text": "Senior engineer with ten years of experience building scalable backend services."})
    out = T.to_english(ZH, kind="resume")
    assert out["source_language"] == "zh"
    assert out["method"] == "llm"
    assert "Senior engineer" in out["english_text"]
    assert 0.0 <= out["confidence"] <= 1.0


def test_translation_failure_degrades_to_original(monkeypatch):
    monkeypatch.setattr(T, "is_live", lambda: True)
    def boom(**k):
        raise RuntimeError("model down")
    monkeypatch.setattr(T, "call_claude_json", boom)
    out = T.to_english(JA)
    assert out["english_text"] == JA  # intake never fails on translation
    assert out["method"] == "passthrough-error"


def test_empty_text():
    out = T.to_english("   ")
    assert out["method"] == "empty"


def test_pivot_restores_the_keyword_signal():
    """The whole point: the deterministic keyword signal is ~0 on non-English
    text, but works once the text is pivoted to English. This proves the
    architecture end-to-end on the real scorer."""
    from app.engines import intake

    # Pure CJK (no Latin tech terms): the English tokenizer sees ZERO content
    # words, so the keyword signal is 0 — the candidate looks like a non-match.
    zh_cv = "拥有十年经验的高级软件工程师，擅长容器编排与分布式系统。"
    zh_jd = "招聘资深软件工程师，需精通容器编排与分布式系统。"
    raw = intake.traditional_ats(zh_jd, zh_cv)["score"]
    assert raw == 0  # broken without the pivot

    # English pivot (what the translator returns) scores properly.
    en_cv = ("Senior software engineer with ten years of experience in container "
             "orchestration and distributed systems.")
    en_jd = ("Hiring a senior software engineer proficient in container "
             "orchestration and distributed systems.")
    pivoted = intake.traditional_ats(en_jd, en_cv)["score"]
    assert pivoted > 0
