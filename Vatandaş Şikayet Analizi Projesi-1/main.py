# main.py — Neutral Corporate v2 + Soft Green Chips (left & right), Blue Buttons

import os
import sys
from typing import List, Dict, Any, Iterable, Tuple
import pandas as pd

from PyQt5.QtCore import Qt, QDate, QUrl, QSize, QRect, QRectF
from PyQt5.QtGui import (
    QColor, QPixmap, QDesktopServices, QCursor, QPalette,
    QFont, QPainter, QLinearGradient
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QGraphicsDropShadowEffect,
    QScrollArea, QFrame, QSizePolicy, QListView, QHeaderView, QSplashScreen
)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# =============== Theme ===============
NAVY        = "#111827"     # headings/dark text
TEXT        = "#374151"     # body text
BORDER_C    = "#E5E7EB"     # card/border

SECTION_TEXT    = "#000000"
SECTION_BG_40   = "#E5E7EB"

RIGHT_BG        = "#FAFAFA"     # right panel bg

# Buttons (sol panel)
SOFT_BLUE_BG    = "#9FD8FF"
SOFT_BLUE_BG_H  = "#8FCFFF"

# ---- CHIP'ler için SOFT YEŞİL GRADYAN ----
SOFT_GREEN_CHIP_BASE = (
    "background: qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5,"
    " stop:0 #F1FFF6, stop:0.35 #E1FAEF, stop:0.7 #C9F4DE, stop:1 #B1ECCF);"
    f" border:1px solid {BORDER_C};"
    " border-radius:10px;"
)
SOFT_GREEN_CHIP_HOVER = (
    "background: qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5,"
    " stop:0 #EBFFF3, stop:0.35 #D3F7E9, stop:0.7 #B9F1D8, stop:1 #9FE8C7);"
)

TABLE_HDR_BG    = "#F3F4F6"
TABLE_HDR_FG    = "#111827"

SELECTION_BG    = "rgba(37, 99, 235, 0.12)"
SELECTION_FG    = TEXT

ALT_ROW_BG      = "#F7F7F7"

BASE_QSS = f"""
QWidget {{
  background:#ffffff; color:{TEXT};
  font-family:'Segoe UI Variable','Inter','Segoe UI','Trebuchet MS',Arial;
  font-size:13.5pt;
}}
QHeaderView::section {{
  background:{TABLE_HDR_BG}; border:none; padding:8px 10px;
  font-weight:800; color:{TABLE_HDR_FG};
}}
QTableWidget {{
  font-size:13pt;
}}
QTableView::item:alternate {{
  background:{ALT_ROW_BG};
}}
QTableView::item:selected {{
  background:{SELECTION_BG}; color:{SELECTION_FG};
}}
"""

def add_shadow(w: QWidget, blur=22, dx=0, dy=8, alpha=100):
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(blur); eff.setOffset(dx, dy); eff.setColor(QColor(0,0,0,alpha))
    w.setGraphicsEffect(eff)

def ellipsize(t: str, n: int = 120) -> str:
    s = (t or "").strip()
    return s if len(s) <= n else s[:n-1] + "…"

def safe_url(u) -> str | None:
    try:
        if u is None: return None
        if isinstance(u, float) and pd.isna(u): return None
    except Exception:
        pass
    if isinstance(u, str):
        s = u.strip()
        return s if s.lower().startswith(("http://", "https://")) else None
    return None

def section_header(text: str) -> QWidget:
    # Left panel section headers: 270° white -> light blue
    wrap = QWidget()
    v = QVBoxLayout(wrap); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(4)
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "QLabel{"
        "background: qlineargradient(spread:pad, x1:1, y1:0.5, x2:0, y2:0.5,"
        " stop:0 #ffffff, stop:1 #adecff);"
        f"color:{SECTION_TEXT};font-weight:700;font-size:12pt; padding:4px 8px; border-radius:6px;"
        "}"
    )
    v.addWidget(lbl)
    bar = QFrame(); bar.setFixedHeight(2)
    bar.setStyleSheet(f"background:{SECTION_BG_40};border-radius:1px;")
    v.addWidget(bar)
    return wrap

class Card(QWidget):
    def __init__(self, content: QWidget):
        super().__init__()
        self.setStyleSheet(f"background:#fff;border:1px solid {BORDER_C};border-radius:14px;")
        add_shadow(self, blur=20, dy=8, alpha=90)
        l = QVBoxLayout(self); l.setContentsMargins(12,12,12,12); l.setSpacing(8)
        l.addWidget(content)

class SmallPopupComboBox(QComboBox):
    def __init__(self, parent=None, max_visible=10, row_h=22, popup_w=240):
        super().__init__(parent)
        self._max_visible=max_visible; self._row_h=row_h; self._popup_w=popup_w
        self.setMaxVisibleItems(max_visible)
        lv = QListView(); lv.setStyleSheet("font-size:10pt;"); lv.setSpacing(0)
        self.setView(lv)
    def showPopup(self):
        super().showPopup()
        try:
            v=self.view(); v.setUniformItemSizes(True)
            vis=min(self.count(), self._max_visible); h=int(vis*self._row_h+6)
            v.setFixedHeight(h); v.setMinimumWidth(self._popup_w)
            v.window().setFixedHeight(h); v.window().setMinimumWidth(self._popup_w)
            v.verticalScrollBar().setVisible(True)
        except Exception: pass

# =============== IMAGE LOADER ===============
class ImageLabel(QLabel):
    _manager: QNetworkAccessManager = None
    def __init__(self, urls: List[str], post_id: str | None = None,
                 size: QSize = QSize(220,220), click_url: str | None = None):
        super().__init__()
        if ImageLabel._manager is None:
            ImageLabel._manager = QNetworkAccessManager()
        self.setFixedSize(size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"border-radius:12px;background:#fff;border:1px solid {BORDER_C};")
        self._click_url = safe_url(click_url)
        if self._click_url:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        self._post_id = post_id
        self._fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN") or os.getenv("FB_ACCESS_TOKEN") or ""
        self._candidates = [u for u in urls if safe_url(u)]
        self._idx = 0
        if self._candidates: self._try(self._candidates[0])
        else: self._resolve_and_try()

    def mousePressEvent(self, e):
        if self._click_url: QDesktopServices.openUrl(QUrl(self._click_url))

    def _resolve_and_try(self):
        if not (self._post_id and self._fb_token):
            self._set_placeholder("Görsel yok"); return
        try:
            import requests
            u1 = f"https://graph.facebook.com/{self._post_id}/picture?redirect=false&access_token={self._fb_token}"
            r1 = requests.get(u1, timeout=10)
            if r1.ok:
                data = r1.json() or {}
                cdn = (((data.get("data") or {}).get("url")))
                if safe_url(cdn):
                    self._candidates = [cdn]; self._idx = 0
                    self._try(self._candidates[0]); return
            u2 = f"https://graph.facebook.com/{self._post_id}?fields=full_picture,picture&type=large&access_token={self._fb_token}"
            r2 = requests.get(u2, timeout=10)
            if r2.ok:
                j = r2.json() or {}
                for k in ("full_picture", "picture"):
                    if safe_url(j.get(k)):
                        self._candidates = [j[k]]; self._idx = 0
                        self._try(self._candidates[0]); return
        except Exception:
            pass
        self._set_placeholder("Görsel yüklenemedi")

    def _try(self, url: str):
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", b"Mozilla/5.0 Chrome/125 Safari/537.36")
        req.setRawHeader(b"Referer", b"https://www.facebook.com/")
        rep = ImageLabel._manager.get(req)
        rep.sslErrors.connect(lambda _errs, r=rep: r.ignoreSslErrors())
        rep.finished.connect(lambda r=rep: self._on_done(r))

    def _on_done(self, rep: QNetworkReply):
        ok = False
        if rep.error() == QNetworkReply.NoError:
            data = rep.readAll(); pm = QPixmap()
            if pm.loadFromData(data):
                pm = pm.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setPixmap(pm); ok = True
        rep.deleteLater()
        if ok: return
        self._idx += 1
        if self._idx < len(self._candidates):
            self._try(self._candidates[self._idx]); return
        if self._post_id and self._fb_token:
            self._resolve_and_try(); return
        self._set_placeholder("Görsel yüklenemedi")

    def _set_placeholder(self, text: str):
        self.setText(f"🖼️  {text}")
        self.setStyleSheet(self.styleSheet()+" QLabel{color:#6b7280; font-size:11.5pt;}")

class ImageCarousel(QWidget):
    def __init__(self, urls: List[str], post_id: str | None, click_url: str | None,
                 size: QSize = QSize(220,220)):
        super().__init__()
        self._urls = [u for u in urls if safe_url(u)]
        self._post_id = post_id; self._click_url = click_url; self._size=size; self._i=0
        self.setFixedSize(size.width()+74, size.height()+14)
        self._box = QWidget(self); self._box.setGeometry(QRect(37,7,size.width(),size.height()))
        lay = QVBoxLayout(self._box); lay.setContentsMargins(0,0,0,0)
        self._img = ImageLabel(self._urls[:1], post_id=self._post_id, size=self._size, click_url=self._click_url)
        lay.addWidget(self._img)

        self._left = QPushButton("‹", self); self._left.setGeometry(QRect(2, int(self.height()/2-20), 30, 40))
        self._right= QPushButton("›", self); self._right.setGeometry(QRect(self.width()-32, int(self.height()/2-20), 30, 40))
        for b in (self._left, self._right):
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet("QPushButton{background:rgba(0,0,0,.26);color:white;border:none;border-radius:7px;"
                            "font-size:18pt;} QPushButton:hover{background:rgba(0,0,0,.36);}")
        self._left.clicked.connect(self.prev); self._right.clicked.connect(self.next)
        self._update_nav()

    def _update_nav(self):
        many = len(self._urls)>1
        self._left.setVisible(many); self._right.setVisible(many)

    def _refresh(self):
        l = self._box.layout()
        while l.count():
            w=l.takeAt(0).widget()
            if w: w.setParent(None)
        cur = self._urls[self._i:self._i+1]
        l.addWidget(ImageLabel(cur, post_id=self._post_id, size=self._size, click_url=self._click_url))

    def next(self):
        if not self._urls: return
        self._i=(self._i+1)%len(self._urls); self._refresh()

    def prev(self):
        if not self._urls: return
        self._i=(self._i-1)%len(self._urls); self._refresh()

# =============== Post feed ===============
class PostCard(QWidget):
    def __init__(self, post_id: str, post_title: str, post_time: str,
                 rows: Iterable[Dict[str, Any]], image_urls: List[str], post_url: str | None):
        super().__init__()
        self.setStyleSheet(f"background:#fff;border:1px solid {BORDER_C};border-radius:14px;")
        add_shadow(self, blur=18, dy=6, alpha=90)

        v = QVBoxLayout(self); v.setContentsMargins(14,14,14,14); v.setSpacing(10)

        header = QWidget()
        header.setStyleSheet(f"background:#fff;border:1px solid {BORDER_C};border-radius:10px;")
        hv = QHBoxLayout(header); hv.setContentsMargins(10,8,10,8); hv.setSpacing(10)

        carousel = ImageCarousel(image_urls, post_id=post_id, click_url=post_url, size=QSize(220,220))
        carousel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hv.addWidget(carousel)

        title_box = QVBoxLayout(); title_box.setSpacing(6)

        # ---- SAĞ PANEL CHIPLER (SOFT YEŞİL) ----
        chip_qss = f"QWidget{{{SOFT_GREEN_CHIP_BASE}}} QWidget:hover{{{SOFT_GREEN_CHIP_HOVER}}}"

        title_chip = QWidget()
        title_chip.setStyleSheet(chip_qss)
        tc_l = QHBoxLayout(title_chip); tc_l.setContentsMargins(10,8,10,8)
        title = QLabel(f"{post_title}")
        title.setStyleSheet("color:#111827; font-size:15.5pt; font-weight:800;")
        tc_l.addWidget(title)
        s_post_url = safe_url(post_url)
        if s_post_url:
            title.setCursor(QCursor(Qt.PointingHandCursor))
            title.mousePressEvent = lambda _e: QDesktopServices.openUrl(QUrl(s_post_url))
        title_box.addWidget(title_chip)

        time_chip = QWidget()
        time_chip.setStyleSheet(chip_qss)
        ts_l = QHBoxLayout(time_chip); ts_l.setContentsMargins(10,8,10,8)
        ts = QLabel(post_time); ts.setStyleSheet("color:#111827; font-size:12.5pt; font-weight:600;")
        ts_l.addWidget(ts)
        title_box.addWidget(time_chip)

        hv.addLayout(title_box, 1)
        v.addWidget(header)

        table = QTableWidget(); table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Yorum", "Tarih", "Mahalle", "Kategori"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget{background:#fff;border:1px solid #e6ebf2;border-radius:10px;}"
            f"QTableWidget::item:selected{{background:{SELECTION_BG}; color:{SELECTION_FG};}}"
        )
        rows_list = list(rows); table.setRowCount(len(rows_list))
        table.verticalHeader().setDefaultSectionSize(32)
        show_rows = max(10, min(16, len(rows_list)))
        table.setMinimumHeight(int(32*show_rows + 50))

        for r, row in enumerate(rows_list):
            msg = row.get("message",""); date = row.get("date","")
            it0 = QTableWidgetItem(ellipsize(msg)); it0.setData(Qt.UserRole, msg)
            it1 = QTableWidgetItem(date.strftime("%Y-%m-%d %H:%M") if hasattr(date,"strftime") else "")
            it2 = QTableWidgetItem(row.get("mahalle","")); it3 = QTableWidgetItem(row.get("kategori",""))
            table.setItem(r,0,it0); table.setItem(r,1,it1); table.setItem(r,2,it2); table.setItem(r,3,it3)
        table.itemDoubleClicked.connect(self._open_full)
        v.addWidget(table)

    def _open_full(self, it: QTableWidgetItem):
        txt = it.data(Qt.UserRole)
        if txt: QMessageBox.information(self, "Yorum", txt)

class PostFeed(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self._wrap = QWidget()
        self._lay = QVBoxLayout(self._wrap); self._lay.setContentsMargins(10,10,10,10); self._lay.setSpacing(16)
        self.setWidget(self._wrap)
    def populate(self, groups: Iterable[Tuple[str,str,str,List[Dict[str,Any]],List[str],str]]):
        while self._lay.count():
            w=self._lay.takeAt(0).widget()
            if w: w.setParent(None)
        for pid,title,ptime,rows,imgs,purl in groups:
            self._lay.addWidget(PostCard(pid,title,ptime,rows,imgs,purl))
        spacer=QFrame(); spacer.setFixedHeight(8); spacer.setStyleSheet("background:transparent;")
        self._lay.addWidget(spacer)

# =============== Project modules ===============
from facebook_client import fetch_posts_with_comments
from models import TextClassifier
from model_kodu import mahalle_bul_olur
from data_store import summarize_by_mahalle, summarize_by_category

# =============== Data ===============
OLUR_MAHALLELER = [
    "Akbayır","Aktepe","Altunkaya","Aşağıçayırlı","Cumhuriyet","Aşağıkaracasu","Atlı",
    "Beğendik","Beşkaya","Boğazgören","Bozdoğan","Hastane","Çataksu","Coşkunlar","Eğlek",
    "Ekinlik","Filizli","Güngöründü","Ilıkaynak","Kaban","Kaledibi","Karaköçlar","Keçili",
    "Kekikli","Köprübaşı","Merkez","Oğuzkent","Olgun","Olurdere","Ormanağzı","Saribaşak",
    "Soğukgöze","Süngübayır","Şalpazarı","Taşgeçit","Taşlıköy","Ürünlü","Uzunharman",
    "Yaylabaşı","Yeşilbağlar","Yıldızkaya","Yolgözler","Yukarıçayırlı","Yukarıkızılkale"
]
COMPLAINT_MODEL_DIR = "./models/sikayet_egitim_modeli"
CATEGORY_MODEL_DIR  = "./models/berturk_kategori_modeli"

# =============== Main Window ===============
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Olur Belediyesi — Şikâyet Analizi")
        self.setStyleSheet(BASE_QSS)
        self.resize(1600, 980)

        try: self.complaint_clf = TextClassifier(COMPLAINT_MODEL_DIR)
        except Exception: self.complaint_clf = None
        try: self.category_clf  = TextClassifier(CATEGORY_MODEL_DIR)
        except Exception: self.category_clf  = None

        self.df: pd.DataFrame | None = None
        self._build_ui()

    def _build_ui(self):
        # Root background gradient: 90° white -> light blue
        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        GRADIENT_QSS = """
        #root {
          background: qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5,
                     stop:0 #ffffff, stop:1 #adecff);
        }
        """
        root.setStyleSheet(GRADIENT_QSS)

        outer = QVBoxLayout(root); outer.setContentsMargins(18,18,18,18); outer.setSpacing(14)

        top = QWidget(); top.setStyleSheet(f"background:#fff;border:1px solid {BORDER_C};border-radius:14px;")
        tl = QHBoxLayout(top); tl.setContentsMargins(18,10,18,10)
        title = QLabel("Olur Belediyesi — Şikâyet Analizi")
        title.setStyleSheet(f"color:{NAVY};font-weight:900;font-size:18pt;letter-spacing:.2px;")
        tl.addWidget(title); tl.addStretch(1)
        outer.addWidget(top); add_shadow(top, blur=16, dy=3, alpha=80)

        content = QWidget(); cl = QHBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.setSpacing(14)
        content.setStyleSheet("background:transparent;")
        outer.addWidget(content, 1)

        # Left panel
        left_card = QWidget()
        left_card.setStyleSheet(f"background:#fff;border:1px solid {BORDER_C};border-radius:14px;")
        left = QVBoxLayout(left_card); left.setContentsMargins(16,16,16,16); left.setSpacing(12)
        add_shadow(left_card, blur=18, dy=4, alpha=110)

        # ===== Button style (Left panel) — soft blue =====
        btn_style = (
            f"QPushButton{{background:{SOFT_BLUE_BG};"
            f"border:1px solid {BORDER_C};border-radius:12px;padding:10px 16px;"
            "font-weight:800;color:#111827;}} "
            f"QPushButton:hover{{background:{SOFT_BLUE_BG_H};}} "
            "QPushButton:pressed{{transform: translateY(1px);}}"
        )

        left.addWidget(section_header("Arama"))
        self.search_edit=QLineEdit(); self.search_edit.setPlaceholderText("Yorum içinde ara… ")
        self.search_edit.setStyleSheet(
            f"QLineEdit{{padding:10px 12px;border-radius:10px;border:1px solid {BORDER_C};background:#fff;color:{TEXT};}}"
            f"QLineEdit:focus{{border:2px solid #2563EB;}}"
        )
        left.addWidget(self.search_edit)

        left.addWidget(section_header("Tarih Aralığı"))
        self.date_from=QDateEdit(calendarPopup=True); self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_to=QDateEdit(calendarPopup=True); self.date_to.setDisplayFormat("yyyy-MM-dd")
        for w in (self.date_from,self.date_to):
            w.setStyleSheet(
                f"QDateEdit{{padding:10px 12px;border-radius:10px;border:1px solid {BORDER_C};background:#fff;color:{TEXT};}}"
                f"QDateEdit:focus{{border:2px solid #2563EB;}}"
                f"QDateEdit QAbstractItemView{{background:white;color:{TEXT};}}"
            )
        today=QDate.currentDate(); self.date_to.setDate(today); self.date_from.setDate(today.addMonths(-1))
        left.addWidget(self.date_from); left.addWidget(self.date_to)

        left.addWidget(section_header("Mahalle"))
        self.cmb_mahalle=SmallPopupComboBox(max_visible=10,row_h=22,popup_w=240)
        self.cmb_mahalle.setStyleSheet(
            f"QComboBox{{padding:10px 12px;border-radius:10px;border:1px solid {BORDER_C};background:#fff;color:{TEXT};}}"
            f"QComboBox:focus{{border:2px solid #2563EB;}}"
            f"QComboBox QAbstractItemView{{background:white;color:{TEXT};font-size:10pt;outline:0;"
            f"selection-background-color:{SELECTION_BG};}}"
            f"QComboBox QAbstractItemView::item{{min-height:22px;}}"
        )
        self.cmb_mahalle.addItem("Tümü", None)
        for n in sorted(OLUR_MAHALLELER): self.cmb_mahalle.addItem(n, n.lower())
        left.addWidget(self.cmb_mahalle)

        # ===== SOL PANEL CHIPLER (SOFT YEŞİL) =====
        chip_row = QHBoxLayout(); chip_row.setSpacing(8)
        self.chip_mahalle = self._make_left_chip("Mahalle: Tümü")
        self.chip_date    = self._make_left_chip(
            f"Tarih: {self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}"
        )
        chip_row.addWidget(self.chip_mahalle)
        chip_row.addWidget(self.chip_date)
        chip_wrap = QWidget(); chip_wrap.setLayout(chip_row)
        left.addWidget(chip_wrap)

        left.addSpacing(6)
        self.btn_fetch=QPushButton("Facebook'tan Yorumları Çek"); self.btn_fetch.setStyleSheet(btn_style)
        left.addWidget(self.btn_fetch)

        row=QHBoxLayout()
        self.btn_show_mh=QPushButton("Mahalleye Göre"); self.btn_show_cat=QPushButton("Kategoriye Göre")
        self.btn_show_mh.setStyleSheet(btn_style); self.btn_show_cat.setStyleSheet(btn_style)
        row.addWidget(self.btn_show_mh); row.addWidget(self.btn_show_cat)
        left.addLayout(row); left.addStretch(1)
        cl.addWidget(left_card, 4)

        # Right panel
        right_back=QWidget()
        right_back.setStyleSheet(f"background:{RIGHT_BG}; border:none; border-radius:14px;")
        rb=QVBoxLayout(right_back); rb.setContentsMargins(0,0,0,0); rb.setSpacing(10)

        head=QWidget(); head.setStyleSheet(f"background:#fff;border-bottom:1px solid {BORDER_C};")
        hl=QHBoxLayout(head); hl.setContentsMargins(4,6,4,6)
        self.right_title=QLabel("Hoş Geldiniz"); self.right_title.setStyleSheet(f"color:{NAVY};font-weight:900;font-size:15.5pt;")
        hl.addWidget(self.right_title); hl.addStretch(1)
        self.btn_back=QPushButton("←  Geri"); self.btn_back.setVisible(False)
        self.btn_back.setStyleSheet(
            f"QPushButton{{background:#F3F4F6;border:1px solid {BORDER_C};color:{NAVY};border-radius:10px;padding:8px 14px;}}"
            f"QPushButton:hover{{background:#E5E7EB;}}"
        ); hl.addWidget(self.btn_back)
        rb.addWidget(head)

        self.right_stack=QStackedWidget(); rb.addWidget(self.right_stack,1)

        # Welcome
        welcome_inner = QLabel(alignment=Qt.AlignCenter)
        welcome_inner.setWordWrap(True)
        welcome_inner.setStyleSheet("QLabel{font-size:14.5pt;line-height:170%;}")
        self.page_welcome_card = Card(welcome_inner)
        self.right_stack.addWidget(self.page_welcome_card)

        # No results
        nores_inner = QLabel(alignment=Qt.AlignCenter)
        nores_inner.setWordWrap(True)
        nores_inner.setStyleSheet("QLabel{font-size:13.5pt;line-height:165%;color:#475569;}")
        self.page_nores_card = Card(nores_inner)
        self.right_stack.addWidget(self.page_nores_card)

        # Feed
        self.post_feed=PostFeed(); self.right_stack.addWidget(self.post_feed)

        # Summaries
        self.table_mh=QTableWidget(); self.table_mh.setColumnCount(2)
        self.table_mh.setHorizontalHeaderLabels(["Mahalle","Şikâyet Sayısı"])
        self._style_summary_table(self.table_mh, count_col=1)
        self.page_mh_card=Card(self.table_mh); self.right_stack.addWidget(self.page_mh_card)

        self.table_cat=QTableWidget(); self.table_cat.setColumnCount(2)
        self.table_cat.setHorizontalHeaderLabels(["Kategori","Şikâyet Sayısı"])
        self._style_summary_table(self.table_cat, count_col=1)
        self.page_cat_card=Card(self.table_cat); self.right_stack.addWidget(self.page_cat_card)

        cl.addWidget(right_back, 6)

        # signals
        self.btn_fetch.clicked.connect(self.fetch_data)
        self.btn_show_mh.clicked.connect(self.show_mh_table)
        self.btn_show_cat.clicked.connect(self.show_cat_table)
        self.btn_back.clicked.connect(self.go_back_to_comments)
        self.search_edit.textChanged.connect(self.apply_filters)
        self.cmb_mahalle.currentIndexChanged.connect(self.apply_filters)
        self.date_from.dateChanged.connect(self.apply_filters)
        self.date_to.dateChanged.connect(self.apply_filters)

        self.update_welcome()
        self._update_left_chips_text()

    # ------- helper: left panel chip -------
    def _make_left_chip(self, text: str) -> QWidget:
        chip = QWidget()
        chip.setStyleSheet(f"QWidget{{{SOFT_GREEN_CHIP_BASE}}} QWidget:hover{{{SOFT_GREEN_CHIP_HOVER}}}")
        lay = QHBoxLayout(chip); lay.setContentsMargins(10,6,10,6); lay.setSpacing(6)
        lbl = QLabel(text); lbl.setStyleSheet("color:#111827; font-size:11.5pt; font-weight:600;")
        lay.addWidget(lbl)
        chip._label = lbl
        return chip

    def _update_left_chips_text(self):
        mh_txt = self.cmb_mahalle.currentText() or "Tümü"
        self.chip_mahalle._label.setText(f"Mahalle: {mh_txt}")
        dr = f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}"
        self.chip_date._label.setText(f"Tarih: {dr}")

    # ------- table style helpers -------
    def _style_summary_table(self, table: QTableWidget, count_col: int):
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(count_col, QHeaderView.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(32)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget{background:#fff;border:1px solid #e6ebf2;border-radius:10px;}"
            f"QTableWidget::item:selected{{background:{SELECTION_BG}; color:{SELECTION_FG};}}"
        )
        h = table.horizontalHeader()
        h.setDefaultAlignment(Qt.AlignCenter)
        table.setMinimumHeight(300)

    # ===== screens =====
    def update_welcome(self):
        total = int(len(self.df)) if isinstance(self.df, pd.DataFrame) else 0
        msg = (f"<b style='color:{NAVY};font-size:18pt;'>Olur Belediyesi — Şikâyet Analizi</b><br><br>"
               f"<ul style='font-size:14pt; line-height:170%; text-align:left; margin:0 24px;'>"
               f"<li>Soldan <b>Facebook'tan Yorumları Çek</b> ile verileri al</li>"
               f"<li>Ardından <b>Mahalleye Göre</b> veya <b>Kategoriye Göre</b> özet tabloları aç</li>"
               f"<li>Yorumlar, gönderilere göre gruplu tablolar halinde listelenir</li>"
               f"</ul><br>"
               f"<span style='font-size:13.5pt;'>Toplam kayıt (bu oturum): <b>{total}</b></span>")
        card_label: QLabel = self.page_welcome_card.findChild(QLabel)
        card_label.setText(msg)
        self.right_title.setText("Hoş Geldiniz")
        self.right_stack.setCurrentWidget(self.page_welcome_card)
        self.update_back_visibility()

    def show_no_results(self, where, q, mh, dr):
        note=(f"<b style='font-size:16pt;color:{NAVY};'>{where}: Sonuç bulunamadı</b><br><br>"
              f"Uygulanan filtrelerle eşleşen kayıt yok.<br><br>"
              f"<span style='color:#475569;'><b>Arama:</b> {q or '(boş)'} &nbsp; "
              f"<b>Mahalle:</b> {mh or 'Tümü'} &nbsp; <b>Tarih:</b> {dr or '(son 1 ay)'}</span>")
        nores_label: QLabel = self.page_nores_card.findChild(QLabel)
        nores_label.setText(note)
        self.right_title.setText(where)
        self.right_stack.setCurrentWidget(self.page_nores_card)
        self.update_back_visibility()

    # ===== data fetch =====
    def fetch_posts_df(self) -> pd.DataFrame:
        bundle = fetch_posts_with_comments(limit_posts=30, limit_comments=300)

        fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN") or os.getenv("FB_ACCESS_TOKEN") or ""
        def image_candidates(post: Dict[str, Any]) -> List[str]:
            c=[]
            pid = post.get("id","")
            if pid and fb_token:
                c.extend([
                    f"https://graph.facebook.com/{pid}/picture?type=large&access_token={fb_token}",
                    f"https://graph.facebook.com/{pid}/picture?type=normal&access_token={fb_token}",
                    f"https://graph.facebook.com/{pid}/picture?width=800&access_token={fb_token}",
                ])
            for k in ("full_picture","picture"):
                if post.get(k): c.append(post[k])
            atts=post.get("attachments") or {}; data=atts.get("data") or []
            if isinstance(data,list) and data:
                d0=data[0]
                m=((d0.get("media") or {}).get("image") or {}).get("src")
                if m: c.append(m)
                subs=(d0.get("subattachments") or {}).get("data") or []
                if isinstance(subs,list):
                    for s in subs:
                        mm=((s.get("media") or {}).get("image") or {}).get("src")
                        if mm: c.append(mm)
                if d0.get("picture"): c.append(d0["picture"])
            uniq=[]
            for u in c:
                su=safe_url(u)
                if su and su not in uniq: uniq.append(su)
            return uniq

        rows=[]
        for item in bundle:
            post=item.get("post",{}) or {}
            pid=post.get("id","")
            pmsg=(post.get("message") or "").strip()
            ptime=post.get("created_time","")
            purl=post.get("permalink_url","")
            pics=image_candidates(post)

            coms=item.get("comments",[]) or []
            if coms:
                for c in coms:
                    rows.append({
                        "post_id":pid,"post_message":pmsg,"post_time":ptime,"post_url":purl,"post_pics":pics,
                        "comment_id":c.get("id",""),"message":(c.get("message") or "").strip(),
                        "created":c.get("created_time",""),"author":(c.get("from",{}) or {}).get("name","")
                    })
            else:
                rows.append({
                    "post_id":pid,"post_message":pmsg,"post_time":ptime,"post_url":purl,"post_pics":pics,
                    "comment_id":"","message":"","created":ptime,"author":""
                })

        df=pd.DataFrame(rows)
        if df.empty: return df
        for col in ("created","post_time"):
            if col in df.columns: df[col]=pd.to_datetime(df[col], errors="coerce")
        df["date"]=df["created"] if "created" in df.columns else pd.NaT

        wl=OLUR_MAHALLELER
        df["mahalle"]= [(mahalle_bul_olur(t, wl) or "") for t in df["message"].astype(str).tolist()]

        try: df["t_sikayet"]=self.complaint_clf.predict(df["message"].tolist()) if self.complaint_clf else ""
        except Exception: df["t_sikayet"]=""
        try: df["kategori"]=self.category_clf.predict(df["message"].tolist()) if self.category_clf else df.get("kategori","")
        except Exception:
            if "kategori" not in df.columns: df["kategori"]=""

        if "post_pics" in df.columns:
            df["post_pics"]=df["post_pics"].apply(lambda x: x if isinstance(x,list) else ([] if pd.isna(x) else [x]))
        else: df["post_pics"]= [[]]
        def sanitize_list(lst):
            out=[]
            for u in lst:
                su=safe_url(u)
                if su and su not in out: out.append(su)
            return out
        df["post_pics"]=df["post_pics"].apply(sanitize_list)
        df["post_url"]=df["post_url"].apply(safe_url)
        return df

    def fetch_data(self):
        try:
            self.df=self.fetch_posts_df()
        except Exception as e:
            self._soft_error("Facebook Hatası", str(e)); return
        if self.df is None or self.df.empty:
            self._soft_info("Bilgi","Hiç kayıt gelmedi."); return
        self.show_comments_page()

    # ===== pages =====
    def show_comments_page(self):
        df=self.get_filtered_df()
        if df is None or df.empty:
            q=(self.search_edit.text() or "").strip()
            mh=self.cmb_mahalle.currentText() if self.cmb_mahalle.currentData() else ""
            dr=f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}"
            self.show_no_results("Yorumlar", q, mh, dr); return

        groups=[]
        df_sorted=df.sort_values(by=["post_time","date"], ascending=False, na_position="last")
        for (pid,pmsg,ptime,purl), g in df_sorted.groupby(["post_id","post_message","post_time","post_url"], dropna=False):
            merged_pics=[]
            for lst in g["post_pics"].tolist():
                if isinstance(lst,list):
                    for u in lst:
                        su=safe_url(u)
                        if su and su not in merged_pics: merged_pics.append(su)
            ptitle=ellipsize(pmsg) if pmsg else (f"Gönderi {pid}" if pid else "Gönderi")
            rows=[{"message":r.get("message",""),"date":r.get("date",None),
                   "mahalle":r.get("mahalle",""),"kategori":r.get("kategori","")} for _,r in g.iterrows()]
            groups.append((pid, ptitle, self._fmt(ptime), rows, merged_pics or [], purl))

        self.post_feed.populate(groups)
        self.right_title.setText("Yorumlar")
        self.right_stack.setCurrentWidget(self.post_feed)
        self.update_back_visibility()

    def show_mh_table(self):
        df=self.get_filtered_df()
        if df is None or df.empty:
            q=(self.search_edit.text() or "").strip()
            mh=self.cmb_mahalle.currentText() if self.cmb_mahalle.currentData() else ""
            dr=f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}"
            self.show_no_results("Mahalle Özeti", q, mh, dr); return
        try:
            g=summarize_by_mahalle(df[df["mahalle"]!=""])
        except Exception:
            tmp=df[df["mahalle"]!=""].copy(); tmp["count"]=1
            g=tmp.groupby("mahalle", as_index=False)["count"].count() if not tmp.empty else pd.DataFrame(columns=["mahalle","count"])

        if g is None or g.empty:
            self.show_no_results("Mahalle Özeti", (self.search_edit.text() or "").strip(),
                                 self.cmb_mahalle.currentText() if self.cmb_mahalle.currentData() else "",
                                 f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}")
            return

        self.table_mh.setRowCount(len(g))
        for r,row in g.reset_index(drop=True).iterrows():
            name = str(row.get("mahalle",""))
            cnt  = str(int(row.get("count",0)))
            self.table_mh.setItem(r,0,QTableWidgetItem(name))
            it = QTableWidgetItem(cnt); it.setTextAlignment(Qt.AlignCenter)
            self.table_mh.setItem(r,1,it)

        self.right_title.setText("Mahalle Özeti"); self.right_stack.setCurrentWidget(self.page_mh_card)
        self.update_back_visibility()

    def show_cat_table(self):
        df=self.get_filtered_df()
        if df is None or df.empty:
            q=(self.search_edit.text() or "").strip()
            mh=self.cmb_mahalle.currentText() if self.cmb_mahalle.currentData() else ""
            dr=f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}"
            self.show_no_results("Kategori Özeti", q, mh, dr); return
        try:
            g=summarize_by_category(df[df["kategori"]!=""])
        except Exception:
            tmp=df[df["kategori"]!=""].copy(); tmp["count"]=1
            g=tmp.groupby("kategori", as_index=False)["count"].count() if not tmp.empty else pd.DataFrame(columns=["kategori","count"])

        if g is None or g.empty:
            self.show_no_results("Kategori Özeti", (self.search_edit.text() or "").strip(),
                                 self.cmb_mahalle.currentText() if self.cmb_mahalle.currentData() else "",
                                 f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}")
            return

        self.table_cat.setRowCount(len(g))
        for r,row in g.reset_index(drop=True).iterrows():
            name = str(row.get("kategori",""))
            cnt  = str(int(row.get("count",0)))
            self.table_cat.setItem(r,0,QTableWidgetItem(name))
            it = QTableWidgetItem(cnt); it.setTextAlignment(Qt.AlignCenter)
            self.table_cat.setItem(r,1,it)

        self.right_title.setText("Kategori Özeti"); self.right_stack.setCurrentWidget(self.page_cat_card)
        self.update_back_visibility()

    def go_back_to_comments(self): self.show_comments_page()

    def update_back_visibility(self):
        cur=self.right_stack.currentWidget()
        self.btn_back.setVisible(not (cur is self.post_feed or cur is self.page_welcome_card))

    def apply_filters(self):
        self._update_left_chips_text()
        if self.df is None: self.update_welcome(); return
        cur=self.right_stack.currentWidget()
        if   cur is self.post_feed: self.show_comments_page()
        elif cur is self.page_mh_card: self.show_mh_table()
        elif cur is self.page_cat_card: self.show_cat_table()
        else: self.show_comments_page()

    def get_filtered_df(self) -> pd.DataFrame | None:
        if self.df is None or self.df.empty: return self.df
        df=self.df.copy()
        try:
            s=self.date_from.date().toPyDate(); e=self.date_to.date().toPyDate()
            if s and e and "date" in df.columns: df=df[(df["date"].dt.date>=s)&(df["date"].dt.date<=e)]
        except Exception: pass
        mh=self.cmb_mahalle.currentData()
        if mh: df=df[df["mahalle"].str.lower()==mh]
        q=(self.search_edit.text() or "").strip().lower()
        if q: df=df[df["message"].str.lower().str.contains(q, na=False)]
        return df

    def _fmt(self, x) -> str:
        try:
            if pd.isna(x): return ""
            if hasattr(x,"strftime"): return x.strftime("%Y-%m-%d %H:%M")
            s=str(x); return s.replace("T"," ").replace("+00:00","").replace("Z","")
        except Exception: return ""

    def _soft_error(self, t, m): QMessageBox(QMessageBox.Warning, t, m, parent=self).exec_()
    def _soft_info (self, t, m): QMessageBox(QMessageBox.Information, t, m, parent=self).exec_()

# ======= App entry: Splash =======
if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion")
    pal=app.palette()
    pal.setColor(QPalette.ButtonText, QColor(NAVY))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.AlternateBase, QColor(ALT_ROW_BG))
    app.setPalette(pal)

    # Splash
    W, H = 900, 500
    splash_pix = QPixmap(W, H)
    splash_pix.fill(Qt.transparent)

    p = QPainter(splash_pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    grad = QLinearGradient(0, 0, W, 0)  # 90°
    grad.setColorAt(0.0, QColor("#ffffff"))
    grad.setColorAt(1.0, QColor("#adecff"))

    # soft outer shadow bar
    p.fillRect(12, 18, W-24, H-24, QColor(0, 0, 0, 45))

    # rounded card
    rect = QRectF(20, 26, W-40, H-52)
    p.setPen(Qt.NoPen)
    p.setBrush(grad)
    p.drawRoundedRect(rect, 22, 22)

    # Title text
    p.setPen(QColor("#0f172a"))
    p.setFont(QFont("Segoe UI", 34, QFont.Black))
    p.drawText(splash_pix.rect().adjusted(0, 60, 0, -160), Qt.AlignHCenter | Qt.AlignTop,
               "Vatandaş Şikâyet Analizi")

    # bottom status
    p.setPen(QColor("#334155"))
    p.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
    p.drawText(splash_pix.rect().adjusted(0, 0, 0, -60), Qt.AlignHCenter | Qt.AlignBottom,
               "Başlatılıyor...")

    p.end()

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.show()
    QApplication.processEvents()

    w=MainWindow(); w.show()
    splash.finish(w)
    sys.exit(app.exec_())
