"""Dựng báo cáo DOCX/PDF từ các tệp noi_dung/*.md (ghép theo tên).

Định dạng: A4, Times New Roman 13pt, giãn dòng 1,5, căn đều, thụt đầu dòng 1,27 cm,
lề trái 3 cm / phải 2 cm / trên–dưới 2 cm, số trang ở giữa phía trên; phần đầu đánh
số La Mã, phần nội dung đánh số Ả Rập bắt đầu từ MỞ ĐẦU.

Chạy từ thư mục gốc repository:
    python docs/report/build_report.py
Cần python-docx, matplotlib và LibreOffice (soffice), poppler-utils (pdftotext).
"""
import copy
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = HERE / "figures"
OUT_DOCX = HERE / "bao_cao_kho_du_lieu_khai_pha.docx"

# ---- Thông tin bìa: sửa tại đây --------------------------------------------------
COVER = {
    "school": "HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG",
    "institute": "VIỆN KHOA HỌC KỸ THUẬT BƯU ĐIỆN",
    "report": "BÀI BÁO CÁO CUỐI KỲ MÔN HỌC",
    "course": "KHO DỮ LIỆU VÀ KHAI PHÁ DỮ LIỆU",
    "topic": "XÂY DỰNG KHO DỮ LIỆU VÀ KHAI PHÁ DỮ LIỆU ĐÁNH GIÁ PHIM MOVIELENS 1M",
    "lecturer": "……………………………",
    "course_code": "……………",
    "students": [("Nguyễn Văn Luân", "B23DCCC106"), ("……………………………", "……………")],
    "place_date": "Hà Nội, 10/2026",
}
# -------------------------------------------------------------------------------------

FONT = "Times New Roman"
BODY_PT = 13
TEXT_WIDTH_CM = 16.0  # 21 - 3 - 2


def set_run_font(run, size=None, bold=None, italic=None, name=FONT, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for att in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(att), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def fmt_par(p, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first=1.27, before=0, after=6, line=1.5,
            left=0, keep_next=False, page_break_before=False):
    pf = p.paragraph_format
    p.alignment = align
    pf.first_line_indent = Cm(first) if first else Cm(0)
    pf.left_indent = Cm(left)
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    pf.keep_with_next = keep_next
    pf.page_break_before = page_break_before
    pf.widow_control = True


INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")


def add_inline(p, text, size=BODY_PT, bold=False, italic=False):
    for part in INLINE.split(text):
        if not part:
            continue
        b, i, mono = bold, italic, False
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, i = part[1:-1], not italic
        elif part.startswith("`") and part.endswith("`"):
            part, mono = part[1:-1], True
        r = p.add_run(part)
        set_run_font(r, size=size - (1 if mono else 0), bold=b, italic=i,
                     name="Courier New" if mono else FONT)
    return p


def add_field(run, instr):
    for tag, text in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
            run._element.append(el)
        elif text == instr:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = instr
            run._element.append(el)
        else:
            el = OxmlElement("w:t")
            el.text = text
            run._element.append(el)


def set_page_numbering(section, fmt, start):
    sectPr = section._sectPr
    pg = sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), str(start))


def setup_section(section, header_number=True):
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin, section.right_margin = Cm(3), Cm(2)
    section.top_margin, section.bottom_margin = Cm(2), Cm(2)
    section.header_distance = Cm(0.9)
    section.header.is_linked_to_previous = False
    hdr = section.header
    p = hdr.paragraphs[0] if hdr.paragraphs else hdr.add_paragraph()
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    if header_number:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run()
        set_run_font(r, size=BODY_PT)
        add_field(r, "PAGE")


def float_picture_behind(doc, paragraph, path, width_cm, height_cm, x_cm, y_cm):
    """Chèn ảnh nổi phía sau chữ, định vị theo trang (khung bìa)."""
    run = paragraph.add_run()
    run.add_picture(str(path), width=Cm(width_cm), height=Cm(height_cm))
    inline = run._element.find(".//" + qn("wp:inline"))
    anchor = OxmlElement("wp:anchor")
    for k, v in dict(distT="0", distB="0", distL="0", distR="0", simplePos="0", relativeHeight="0",
                     behindDoc="1", locked="0", layoutInCell="1", allowOverlap="1").items():
        anchor.set(k, v)
    sp = OxmlElement("wp:simplePos")
    sp.set("x", "0")
    sp.set("y", "0")
    anchor.append(sp)
    for tag, rel, off in (("wp:positionH", "page", x_cm), ("wp:positionV", "page", y_cm)):
        el = OxmlElement(tag)
        el.set("relativeFrom", rel)
        o = OxmlElement("wp:posOffset")
        o.text = str(int(Cm(off)))
        el.append(o)
        anchor.append(el)
    anchor.append(copy.deepcopy(inline.find(qn("wp:extent"))))
    ee = OxmlElement("wp:effectExtent")
    for k in ("l", "t", "r", "b"):
        ee.set(k, "0")
    anchor.append(ee)
    anchor.append(OxmlElement("wp:wrapNone"))
    for tag in ("wp:docPr", "wp:cNvGraphicFramePr", "a:graphic"):
        anchor.append(copy.deepcopy(inline.find(qn(tag))))
    inline.getparent().replace(inline, anchor)


def cover(doc):
    sec = doc.sections[0]
    setup_section(sec, header_number=False)
    sec.top_margin = Cm(3.2)
    sec.left_margin = sec.right_margin = Cm(2.5)
    first = doc.add_paragraph()
    float_picture_behind(doc, first, FIG / "cover_frame.png", 18.6, 27.4, 1.2, 1.15)
    fmt_par(first, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, after=0, line=1.15)
    r = first.add_run(COVER["school"])
    set_run_font(r, size=14, bold=True)
    p = doc.add_paragraph()
    fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, after=18, line=1.15)
    set_run_font(p.add_run(COVER["institute"]), size=14, bold=True)
    p = doc.add_paragraph()
    fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, after=24, line=1.0)
    p.add_run().add_picture(str(FIG / "logo_ptit.png"), height=Cm(3.0))
    p.add_run("      ")
    p.add_run().add_picture(str(FIG / "logo_ript.png"), height=Cm(3.0))
    for txt, size, after in ((COVER["report"], 17, 2), (COVER["course"], 17, 18)):
        p = doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, after=after, line=1.15)
        set_run_font(p.add_run(txt), size=size, bold=True)
    p = doc.add_paragraph()
    fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, after=18, line=1.2, left=0.8)
    p.paragraph_format.right_indent = Cm(0.8)
    set_run_font(p.add_run("ĐỀ TÀI: "), size=14, bold=True)
    set_run_font(p.add_run(COVER["topic"]), size=14, bold=True, color="1F4E79")
    for label, val in (("GIẢNG VIÊN: ", COVER["lecturer"]), ("MÃ HỌC PHẦN: ", COVER["course_code"])):
        p = doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, after=2, line=1.15)
        set_run_font(p.add_run(label), size=14, bold=True)
        set_run_font(p.add_run(val), size=14, bold=True)
    p = doc.add_paragraph()
    fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, before=22, after=8, line=1.15)
    set_run_font(p.add_run("THÔNG TIN SINH VIÊN:"), size=14, bold=True)
    t = doc.add_table(rows=1 + len(COVER["students"]), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(("HỌ VÀ TÊN", "MÃ SINH VIÊN")):
        c = t.rows[0].cells[j]
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(c.paragraphs[0].add_run(h), size=14, bold=True)
    for i, (n, m) in enumerate(COVER["students"], start=1):
        for j, v in enumerate((n, m)):
            c = t.rows[i].cells[j]
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_run_font(c.paragraphs[0].add_run(v), size=14)
    fix_widths(t, [7, 5])
    # Bảng sinh viên trên bìa không kẻ khung
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "nil")
        borders.append(e)
    t._tbl.tblPr.append(borders)
    # Đẩy dòng địa danh xuống cuối trang
    p = doc.add_paragraph()
    fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, before=110, after=0, line=1.0)
    set_run_font(p.add_run(COVER["place_date"]), size=14, bold=True)


def fix_widths(t, widths):
    """Cố định độ rộng cột (Word và LibreOffice đều tôn trọng)."""
    t.autofit = False
    tbl = t._tbl
    tblPr = tbl.tblPr
    tw = tblPr.find(qn("w:tblW"))
    if tw is None:
        tw = OxmlElement("w:tblW")
        tblPr.append(tw)
    tw.set(qn("w:w"), str(int(sum(widths) * 567)))
    tw.set(qn("w:type"), "dxa")
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    grid = tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[j] * 567)))
    for row in t.rows:
        for j, w in enumerate(widths):
            row.cells[j].width = Cm(w)


class Builder:
    def __init__(self, page_map=None):
        self.doc = Document()
        st = self.doc.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(BODY_PT)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        self.page_map = page_map or {}
        self.toc, self.figs, self.tabs = [], [], []
        self.eq_dir = Path(tempfile.mkdtemp())
        self.eq_n = 0
        self.in_body = False
        self.fresh = False  # vừa sang section mới: tiêu đề kế tiếp không cần ngắt trang

    # ---- các khối nội dung ----
    def title_center(self, text, toc_level=None, size=14, new_page=True, after=12):
        p = self.doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, before=0, after=after, line=1.3,
                keep_next=True, page_break_before=new_page and not self.fresh)
        self.fresh = False
        set_run_font(p.add_run(text), size=size, bold=True)
        if toc_level:
            self.toc.append((toc_level, text))
        return p

    def heading(self, text, level):
        p = self.doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first=0, before=6, after=3, keep_next=True)
        set_run_font(p.add_run(text), size=BODY_PT, bold=True, italic=(level == 3))
        self.toc.append((level, text))

    def subhead(self, text):
        p = self.doc.add_paragraph()
        fmt_par(p, first=1.27, before=3, after=3, keep_next=True)
        add_inline(p, text, bold=True)

    def para(self, text):
        p = self.doc.add_paragraph()
        fmt_par(p)
        add_inline(p, text)

    def bullet(self, text):
        p = self.doc.add_paragraph()
        fmt_par(p, first=-0.6, left=1.87, after=3)
        add_inline(p, "–\u00a0" + text)

    def caption(self, text, kind):
        p = self.doc.add_paragraph()
        keep = kind == "tab"
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, before=3 if kind == "fig" else 6,
                after=9 if kind == "fig" else 3, line=1.2, keep_next=keep)
        m = re.match(r"((?:Hình|Bảng) \d+\.\d+\.)\s*(.*)", text)
        if m:
            set_run_font(p.add_run(m.group(1) + " "), size=BODY_PT, bold=True)
            set_run_font(p.add_run(m.group(2)), size=BODY_PT, italic=False)
        else:
            set_run_font(p.add_run(text), size=BODY_PT)
        if self.in_body:
            (self.figs if kind == "fig" else self.tabs).append(text)

    def figure(self, path, cap, width):
        full = (HERE / path) if not Path(path).is_absolute() else Path(path)
        if not full.exists():
            full = ROOT / path
        p = self.doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, before=6, after=0, line=1.0,
                keep_next=True)
        p.add_run().add_picture(str(full), width=Cm(width))
        self.caption(cap, "fig")

    def equation(self, latex):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        matplotlib.rcParams["mathtext.fontset"] = "stix"
        self.eq_n += 1
        fn = self.eq_dir / f"eq{self.eq_n}.png"
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, f"${latex}$", fontsize=17)
        fig.savefig(fn, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
        plt.close(fig)
        from PIL import Image
        w, h = Image.open(fn).size
        p = self.doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, first=0, before=3, after=6, line=1.0)
        p.add_run().add_picture(str(fn), width=Cm(min(w / 300 * 2.54, TEXT_WIDTH_CM - 1)))

    def table(self, cap, rows, widths=None, font=11.5):
        self.caption(cap, "tab")
        ncol = len(rows[0])
        t = self.doc.add_table(rows=len(rows), cols=ncol)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        numeric = re.compile(r"^[−\-+]?[\d.,%]+(\s?%)?$|^—$")
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                c = t.rows[i].cells[j]
                p = c.paragraphs[0]
                fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, first=0, before=1, after=1, line=1.1)
                if i == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_inline(p, val, size=font, bold=True)
                    sh = OxmlElement("w:shd")
                    sh.set(qn("w:val"), "clear")
                    sh.set(qn("w:color"), "auto")
                    sh.set(qn("w:fill"), "D9E2F3")
                    c._tc.get_or_add_tcPr().append(sh)
                else:
                    if numeric.match(val.strip()):
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_inline(p, val, size=font)
            if i == 0:
                trPr = t.rows[0]._tr.get_or_add_trPr()
                th = OxmlElement("w:tblHeader")
                trPr.append(th)
        fix_widths(t, widths or [TEXT_WIDTH_CM / ncol] * ncol)
        # Bảng ngắn: giữ trọn trên một trang; mọi dòng không bị cắt ngang
        for i, row in enumerate(t.rows):
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            if len(rows) <= 16 and i < len(rows) - 1:
                for c in row.cells:
                    for p in c.paragraphs:
                        p.paragraph_format.keep_with_next = True
        sp = self.doc.add_paragraph()
        fmt_par(sp, first=0, after=0, line=1.0)
        sp.paragraph_format.space_after = Pt(4)

    def code(self, lines):
        t = self.doc.add_table(rows=1, cols=1)
        t.style = "Table Grid"
        fix_widths(t, [TEXT_WIDTH_CM])
        c = t.rows[0].cells[0]
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear")
        sh.set(qn("w:fill"), "F2F2F2")
        c._tc.get_or_add_tcPr().append(sh)
        c.paragraphs[0]._element.getparent().remove(c.paragraphs[0]._element)
        for ln in lines:
            p = c.add_paragraph()
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, first=0, after=0, line=1.0)
            r = p.add_run(ln if ln else " ")
            set_run_font(r, size=9, name="Courier New")
        sp = self.doc.add_paragraph()
        fmt_par(sp, first=0, after=2, line=1.0)

    # ---- danh mục ----
    def toc_line(self, text, level, page, bold=False, indent_cm=0.0):
        p = self.doc.add_paragraph()
        fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, first=0, left=indent_cm, after=2, line=1.3)
        p.paragraph_format.right_indent = Cm(0)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT,
                                                  WD_TAB_LEADER.DOTS)
        # Dòng dài xuống dòng thì thụt treo cho đẹp
        set_run_font(p.add_run(text + "\t" + str(page)), size=BODY_PT, bold=bold)

    def front_lists(self, toc, figs, tabs):
        self.title_center("MỤC LỤC", new_page=True)
        for level, text in toc:
            pg = self.page_map.get(("h", text), "")
            if level == 1:
                self.toc_line(text, 1, pg, bold=True)
            else:
                self.toc_line(text, level, pg, indent_cm=0.5 * (level - 1))
        self.title_center("DANH MỤC HÌNH VẼ", new_page=True)
        for f in figs:
            self.toc_line(f, 2, self.page_map.get(("f", f), ""))
        self.title_center("DANH MỤC BẢNG BIỂU", new_page=True)
        for t in tabs:
            self.toc_line(t, 2, self.page_map.get(("t", t), ""))


def parse_and_build(b, src, prepass):
    lines = []
    for f in sorted(src.glob("*.md")):
        lines += f.read_text(encoding="utf-8").splitlines() + [""]
    i = 0
    buf = []

    def flush():
        if buf:
            b.para(" ".join(s.strip() for s in buf))
            buf.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith("<!--"):
            while "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if not s:
            flush()
        elif s.startswith("@front "):  # trang đầu không vào mục lục (lời nói đầu, từ viết tắt)
            flush()
            b.title_center(s[7:].strip(), new_page=True)
        elif s == "@lists":
            flush()
            b.front_lists(prepass["toc"], prepass["figs"], prepass["tabs"])
        elif s == "@body":
            flush()
            sec = b.doc.add_section(WD_SECTION.NEW_PAGE)
            setup_section(sec)
            set_page_numbering(sec, "decimal", 1)
            b.fresh = True
            b.in_body = True
        elif s.startswith("@chapter "):
            flush()
            b.title_center(s[9:].strip(), toc_level=1, new_page=True)
        elif s.startswith("#### "):
            flush()
            b.subhead(s[5:])
        elif s.startswith("### "):
            flush()
            b.heading(s[4:], 3)
        elif s.startswith("## "):
            flush()
            b.heading(s[3:], 2)
        elif s.startswith("- "):
            flush()
            b.bullet(s[2:])
        elif s.startswith("@fig "):
            flush()
            path, cap, width = [x.strip() for x in s[5:].split("|")]
            b.figure(path, cap, float(width))
        elif s.startswith("@eq "):
            flush()
            b.equation(s[4:].strip())
        elif s.startswith("@table "):
            flush()
            cap = s[7:].strip()
            widths = None
            rows = []
            i += 1
            while i < len(lines) and lines[i].strip():
                t = lines[i].strip()
                if t.startswith("@widths "):
                    widths = [float(x) for x in t[8:].split(",")]
                elif t.startswith("|") and not re.match(r"^\|[\s:\-|]+\|$", t):
                    rows.append([c.strip() for c in t.strip("|").split("|")])
                i += 1
            b.table(cap, rows, widths)
            continue
        elif s == "@code":
            flush()
            code = []
            i += 1
            while lines[i].strip() != "@endcode":
                code.append(lines[i].rstrip())
                i += 1
            b.code(code)
        elif s == "@pagebreak":
            flush()
            b.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        else:
            buf.append(s)
        i += 1
    flush()


def build(page_map, prepass):
    b = Builder(page_map)
    cover(b.doc)
    sec = b.doc.add_section(WD_SECTION.NEW_PAGE)
    setup_section(sec)
    set_page_numbering(sec, "lowerRoman", 1)
    b.fresh = True
    parse_and_build(b, HERE / "noi_dung", prepass)
    b.doc.save(OUT_DOCX)
    return b


def to_pdf(docx):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent),
                    str(docx)], check=True, capture_output=True)
    return docx.with_suffix(".pdf")


def norm(s):
    return re.sub(r"[^0-9a-zà-ỹđ]", "", s.lower())


def page_texts(pdf):
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                         capture_output=True, text=True).stdout
    return [norm(p) for p in out.split("\f")]


def locate(pdf, b):
    pages = page_texts(pdf)
    # Trang có số 1 Ả Rập = trang "MỞ ĐẦU"
    body_start = next(i for i, t in enumerate(pages) if t.startswith("1mởđầu") or "1mởđầu" in t[:12])
    pm = {}
    cursor = body_start
    for kind, items in (("h", [t for _, t in b.toc]), ):
        for t in items:
            key = norm(t)[:45]
            for j in range(cursor, len(pages)):
                if key in pages[j]:
                    pm[(kind, t)] = j - body_start + 1
                    cursor = j
                    break
    for kind, items in (("f", b.figs), ("t", b.tabs)):
        cursor = body_start
        for t in items:
            key = norm(t)[:45]
            for j in range(cursor, len(pages)):
                if key in pages[j]:
                    pm[(kind, t)] = j - body_start + 1
                    cursor = j
                    break
    return pm, len(pages)


def main():
    # Lượt 1: thu thập mục lục/hình/bảng
    b0 = Builder()
    cover(b0.doc)
    parse_and_build(b0, HERE / "noi_dung", {"toc": [], "figs": [], "tabs": []})
    prepass = {"toc": b0.toc, "figs": b0.figs, "tabs": b0.tabs}
    page_map = {}
    for it in range(3):
        b = build(page_map, prepass)
        pdf = to_pdf(OUT_DOCX)
        new_map, n = locate(pdf, b)
        missing = [k for k in [("h", t) for _, t in b.toc] + [("f", f) for f in b.figs]
                   + [("t", t) for t in b.tabs] if k not in new_map]
        if new_map == page_map:
            break
        page_map = new_map
    b = build(page_map, prepass)
    pdf = to_pdf(OUT_DOCX)
    print(f"PDF {n} trang; mục lục {len(b.toc)} mục, {len(b.figs)} hình, {len(b.tabs)} bảng")
    if missing:
        print("Không định vị được:", missing, file=sys.stderr)


if __name__ == "__main__":
    main()
