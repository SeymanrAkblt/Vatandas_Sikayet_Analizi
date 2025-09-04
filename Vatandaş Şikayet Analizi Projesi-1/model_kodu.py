# model_kodu.py  — GÜNCELLENMİŞ
import re
from typing import List, Tuple, Optional

# ---- Mahalle bul (regex tabanlı) ----
_MAH_PTRNS = [
    r"(?P<name>[A-Za-zÇĞİÖŞÜçğıöşü\s\-']{2,})\s*(?:mah(?:\.|allesi)?|mh\.?)\b",
    r"\bmah(?:\.|allesi)?\s*(?P<name>[A-Za-zÇĞİÖŞÜçğıöşü\s\-']{2,})\b",
    r"\b(?P<name>[A-Za-zÇĞİÖŞÜçğıöşü][A-Za-zÇĞİÖŞÜçğıöşü\s\-']+)\b\s*(?:köyü|mezrası)\b",
]

def _clean_name(s: str) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"\b(mah|mah\.|mahallesi|mh\.)$", "", s, flags=re.IGNORECASE).strip()
    return " ".join([w.capitalize() for w in s.split()])

def mahalle_bul(text: str) -> Optional[str]:
    if not isinstance(text, str) or not text.strip():
        return None
    t = " " + text.strip() + " "
    for pat in _MAH_PTRNS:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m and m.group("name"):
            name = _clean_name(m.group("name"))
            if len(name) >= 2:
                return name
    return None

# ---- (Opsiyonel) Kendi modellerini yine kullanmak istersen LAZY yükle ----
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

_tokenizer_sikayet = _model_sikayet = None
_tokenizer_kategori = _model_kategori = None
_id2label_sikayet = {}
_id2label_kategori = {}

def load_local_models(complaint_dir: str, category_dir: str):
    """Yerel klasörden (internet yok) modelleri yükler."""
    global _tokenizer_sikayet, _model_sikayet, _tokenizer_kategori, _model_kategori, _id2label_sikayet, _id2label_kategori
    _tokenizer_sikayet = AutoTokenizer.from_pretrained(complaint_dir, local_files_only=True)
    _model_sikayet     = AutoModelForSequenceClassification.from_pretrained(complaint_dir, local_files_only=True)
    _tokenizer_kategori = AutoTokenizer.from_pretrained(category_dir, local_files_only=True)
    _model_kategori     = AutoModelForSequenceClassification.from_pretrained(category_dir, local_files_only=True)
    _id2label_sikayet = _model_sikayet.config.id2label
    _id2label_kategori = _model_kategori.config.id2label

def analiz_et(texts: List[str]) -> Tuple[List[str], List[str]]:
    """İstersen main.py’den çağır. Öncesinde load_local_models(...) çağrılmalı."""
    assert _model_sikayet is not None and _model_kategori is not None, "Modeller yüklenmedi. load_local_models(...) çağır."
    if isinstance(texts, str):
        texts = [texts]
    with torch.no_grad():
        inp = _tokenizer_sikayet(texts, padding=True, truncation=True, max_length=160, return_tensors="pt")
        s_logits = _model_sikayet(**inp).logits
        pred_s = torch.argmax(s_logits, dim=-1).cpu().numpy().tolist()
        sikayetler = [_id2label_sikayet[int(i)] for i in pred_s]

        inp2 = _tokenizer_kategori(texts, padding=True, truncation=True, max_length=160, return_tensors="pt")
        k_logits = _model_kategori(**inp2).logits
        pred_k = torch.argmax(k_logits, dim=-1).cpu().numpy().tolist()
        kategoriler = [_id2label_kategori[int(i)] for i in pred_k]

    return sikayetler, kategoriler
# ====== Olur whitelist tabanlı mahalle bulucu ======
# Sadece verdiğin mahalle/köy listesinden birini döndürür.
# "mah./mahallesi/mh.", "köyü/mezrası" kalıplarını da destekler.

import re
try:
    from rapidfuzz import process, fuzz
    _RF = True
except Exception:
    _RF = False

_IGNORE_TOKENS = {
    # 'mah' geçen ama mahalle olmayan örnekleri engelle (isteğe göre genişletebilirsin)
    "mahcup", "mahkum", "mahalleli", "mahsul", "mahsus", "mahsuru"
}

def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\wçğıöşü\-\' ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def mahalle_bul_olur(text: str, whitelist: list[str]) -> str | None:
    """
    Yalnızca whitelist'teki isimleri döndürür.
    Sıra:
      1) '... mah./mahallesi/mh.' KALIBI + whitelist eşleşmesi
      2) Metinde whitelist isminin tam kelime geçişi
      3) (Varsa) Fuzzy eşleşme (yüksek eşik)
    Hiçbiri yoksa None.
    """
    if not isinstance(text, str) or not text.strip() or not whitelist:
        return None

    tlow = " " + _norm(text) + " "
    # 'mah' geçen ama mahalle olmayan kelimeleri erken ele
    for bad in _IGNORE_TOKENS:
        if f" {bad} " in tlow:
            return None

    # whitelist'i normalize et
    wl = [_norm(w) for w in whitelist if w and w.strip()]
    # varyantları kapsayan regex kalıbı
    pat = re.compile(r"([a-zçğıöşü0-9\-\']{2,}(?:\s+[a-zçğıöşü0-9\-\']{2,})*)\s+(mah(?:\.|allesi)?|mh\.?|köyü|mezrası)\b")

    # 1) kalıp: "X mah(., mahallesi, mh.)" / "X köyü/mezrası"
    m = pat.search(tlow)
    if m:
        cand = _norm(m.group(1))
        # önce doğrudan whitelist kapsaması
        for w in wl:
            if f" {w} " in f" {cand} " or f" {cand} " in f" {w} ":
                return " ".join(t.capitalize() for t in w.split())
        # fuzzy (yüksek eşik)
        if _RF:
            hit = process.extractOne(cand, wl, scorer=fuzz.token_set_ratio)
            if hit and hit[1] >= 92:
                w = hit[0]
                return " ".join(t.capitalize() for t in w.split())

    # 2) whitelist ismi metinde tam kelime olarak geçiyorsa
    for w in wl:
        if f" {w} " in tlow:
            return " ".join(t.capitalize() for t in w.split())

    # 3) genel fuzzy (çok yüksek eşik; yanlış pozitifleri engeller)
    if _RF:
        hit = process.extractOne(tlow, wl, scorer=fuzz.token_set_ratio)
        if hit and hit[1] >= 94:
            w = hit[0]
            return " ".join(t.capitalize() for t in w.split())

    return None
# ====== /Olur whitelist tabanlı mahalle bulucu ======

