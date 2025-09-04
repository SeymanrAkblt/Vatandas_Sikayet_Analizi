# ner_extractor.py
from __future__ import annotations
from typing import Dict, Tuple, Optional, List
import re
from rapidfuzz import process, fuzz

def _norm(s: str) -> str:
    s = s.lower()
    # sadeleştirme
    s = re.sub(r"[\.\,\!\?\:\;\'\"\(\)\[\]\{\}\-_/]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _build_variants(name: str) -> List[str]:
    # "yeşil mahalle" -> ["yeşil mahalle", "yeşil mahallesi", "yeşil mh", "yeşil mh.", "yeşil mah."]
    base = name.lower().strip()
    roots = [base]
    if base.endswith(" mahallesi"):
        root = base.replace(" mahallesi", "")
        roots.append(root)
    elif base.endswith(" mahalle"):
        root = base.replace(" mahalle", "")
        roots.append(root)

    variants = set()
    for r in roots:
        r = r.strip()
        variants.update([
            r, f"{r} mahallesi", f"{r} mahalle", f"{r} mh", f"{r} mh.", f"{r} mah."
        ])
    return list(variants)

class MahalleNER:
    """
    spaCy TR + EntityRuler + gazetteer + fuzzy fallback
    """
    def __init__(self, mahalle_coords: Dict[str, Tuple[float,float]]):
        self.mahalle_coords = mahalle_coords  # key: lower-case mahalle adı
        self._setup_spacy()
        self._setup_ruler()

        # hızlı eşleşme için isim listesi
        self._names_lc = list(self.mahalle_coords.keys())

    def _setup_spacy(self):
        try:
            import spacy
            try:
                self.nlp = spacy.load("tr_core_news_lg")
            except Exception:
                self.nlp = spacy.load("tr_core_news_sm")
        except Exception:
            import spacy
            self.nlp = spacy.blank("tr")  # en kötü ihtimal boş model

    # def _setup_ruler(self):
    #     from spacy.pipeline import EntityRuler
    #     ruler = EntityRuler(self.nlp, overwrite_ents=True)
    #     patterns = []
    #     # mahalle isimlerinden varyant kalıplar üret
    #     for name_lc in self.mahalle_coords.keys():
    #         for v in _build_variants(name_lc):
    #             patterns.append({"label": "LOC_MAHALLE", "pattern": v})
    #     ruler.add_patterns(patterns)
    #     # boru hattında NER'den önce olsun
    #     self.nlp.add_pipe(ruler, name="mahalle_ruler", before="ner" if "ner" in self.nlp.pipe_names else None)

    def _setup_ruler(self):
    # 'ner' varsa ondan önce ekle, yoksa sona
        before = "ner" if "ner" in self.nlp.pipe_names else None

    # 1) EntityRuler'ı fabrika adıyla ekle
        if "mahalle_ruler" in self.nlp.pipe_names:
            self.nlp.remove_pipe("mahalle_ruler")
        self.nlp.add_pipe("entity_ruler", name="mahalle_ruler", before=before)

    # 2) Ruler'ı al ve pattern'ları ekle
        ruler = self.nlp.get_pipe("mahalle_ruler")

        patterns = []
        for name_lc in self.mahalle_coords.keys():
            for v in _build_variants(name_lc):
                patterns.append({"label": "LOC_MAHALLE", "pattern": v})

    # Bazı sürümlerde initialize gerekir
        try:
            ruler.initialize(lambda: [])
        except Exception:
            pass

        ruler.add_patterns(patterns)


    def find_first(self, text: str) -> Optional[str]:
        """
        Metinden ilk bulunan mahalleyi (orijinal mahallenin title-case hali) döner.
        Sıra: EntityRuler/NER -> cümle içi tam-geçiş -> fuzzy fallback.
        """
        if not isinstance(text, str) or not text.strip():
            return None
        doc = self.nlp(text)

        # 1) EntityRuler / NER ile yakala
        for ent in doc.ents:
            if ent.label_ in ("LOC", "GPE", "LOC_MAHALLE"):
                hit = _norm(ent.text)
                # tam eşleşme (normalizasyonlu)
                # en uzun eşleşeni bul
                candidates = [n for n in self._names_lc if hit == _norm(n) or hit in _norm(n) or _norm(n) in hit]
                if candidates:
                    chosen = sorted(candidates, key=len, reverse=True)[0]
                    return chosen.title()

        # 2) Cümle içinde ham arama (gazetteer)
        tnorm = f" {_norm(text)} "
        direct_hits = [n for n in self._names_lc if f" {_norm(n)} " in tnorm]
        if direct_hits:
            chosen = sorted(direct_hits, key=len, reverse=True)[0]
            return chosen.title()

        # 3) Fuzzy fallback (en yakın mahalle ismi, eşik: 88)
        match, score, _ = process.extractOne(
            _norm(text), self._names_lc, scorer=fuzz.token_set_ratio
        ) if self._names_lc else (None, 0, None)
        if match and score >= 88:
            return match.title()

        return None
