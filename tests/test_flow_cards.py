"""书页式连续排版引擎的回归测试（纯函数部分，不依赖 Chrome）。"""

from render.flow_cards import (
    Layout,
    article_text,
    build_units,
    em_len,
    flow_page_html,
    paginate,
    wrap,
)

L = Layout()  # 定稿默认参数


def test_wrap_basic_and_capacity():
    lines = wrap("一" * 50, L.line_cap)
    assert all(len(ln) <= L.line_cap for ln in lines)
    assert "".join(lines) == "一" * 50  # 零丢失


def test_wrap_no_line_start_punctuation():
    text = "这是一个测试，里面有各种标点。比如逗号、顿号、句号，还有问号？和感叹号！都会触发禁则。"
    for _ in range(20):  # 多种 cap 下都要满足
        lines = wrap(text, 12)
        assert all(ln[0] not in FORBIDDEN_START_SET for ln in lines)


def test_wrap_dash_pair_not_split():
    lines = wrap("前面的话——后面的话", 8)
    joined = "".join(lines)
    assert joined == "前面的话——后面的话"
    assert not any(ln.startswith("—") and len(ln) == 1 for ln in lines)  # 破折号不成单


def test_em_len_latin_conservative():
    assert em_len("m") > em_len("i")  # 宽字母更宽
    assert em_len("中") == 1.0


def test_paginate_zero_loss():
    sections = [
        {"heading": "第一节标题", "paragraphs": ["字" * 120, "词" * 80]},
        {"heading": "第二节标题", "paragraphs": ["句" * 200]},
        {"heading": "第三节标题", "paragraphs": ["段" * 150, "落" * 90]},
    ]
    units = build_units(sections, L)
    pages = paginate(units, L)
    # 零丢失：所有行都在某一页上
    src_lines = [ln for u in units if u["kind"] != "gap" for ln in u["lines"]]
    page_lines = [ln for pg in pages for u in pg if u["kind"] != "gap" for ln in u["lines"]]
    assert src_lines == page_lines
    # 每页不超版心
    for pg in pages:
        assert sum(
            len(u["lines"]) * (L.lh_head if u["kind"] == "h" else L.lh_body) if u["kind"] != "gap" else u["h"]
            for u in pg
        ) <= L.content_h


def test_paginate_heading_not_orphaned():
    sections = [{"heading": f"第{i}节标题", "paragraphs": ["字" * 200]} for i in range(6)]
    units = build_units(sections, L)
    pages = paginate(units, L)
    for pg in pages[:-1]:  # 非末页
        for i, u in enumerate(pg):
            if u["kind"] == "h":
                # 标题后至少跟 2 行正文（同页）
                rest = pg[i + 1:]
                p_lines = sum(len(x["lines"]) for x in rest if x["kind"] == "p")
                assert p_lines >= 2


def test_prose_mode_no_headings():
    sections = [{"heading": "被忽略的标题", "paragraphs": ["字" * 100]}]
    units = build_units(sections, L, use_headings=False)
    assert all(u["kind"] != "h" for u in units)


def test_heading_numbering():
    sections = [{"heading": f"第{i}节", "paragraphs": ["字" * 50]} for i in range(3)]
    units = build_units(sections, L)
    heads = [u for u in units if u["kind"] == "h"]
    assert heads[0]["lines"][0].startswith("一、")
    assert heads[1]["lines"][0].startswith("二、")
    assert heads[2]["lines"][0].startswith("三、")


def test_article_text_roundtrip():
    sections = [
        {"heading": "标题甲", "paragraphs": ["第一段。", "第二段。"]},
        {"heading": "标题乙", "paragraphs": ["第三段。"]},
    ]
    text = article_text(sections)
    assert "一、标题甲" in text
    assert "二、标题乙" in text
    assert "第一段。" in text
    prose = article_text(sections, use_headings=False)
    assert "标题甲" not in prose


def test_page_html_structure():
    units = [{"kind": "p", "lines": ["一行", "两行"]}]
    html = flow_page_html(L, units)
    assert 'class="pln"' in html and 'class="pln last"' in html
    assert "Noto Serif SC" in html


FORBIDDEN_START_SET = set("，。、；：？！」』）】〉》…,.;:?!)]}")
