# data_store.py
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os, re

def load_mahalle_coords(csv_path: str) -> Dict[str, Tuple[float,float]]:
    if not os.path.exists(csv_path):
        # örnek/yer tutucu
        df = pd.DataFrame([
            {"mahalle":"Yeni Mahalle","lat":37.0001,"lon":35.3213},
            {"mahalle":"Eski Mahalle","lat":37.0050,"lon":35.3300},
        ])
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    d = {}
    for _, r in df.iterrows():
        d[str(r["mahalle"]).strip().lower()] = (float(r["lat"]), float(r["lon"]))
    return d

def parse_mahalle(text: str, known_names: List[str]) -> Optional[str]:
    if not isinstance(text, str): return None
    t = " " + text.lower() + " "
    hits = [m for m in known_names if f" {m} " in t]
    if not hits:
        # basit fuzzy: tire/ek kaldırma
        t2 = re.sub(r"[^a-zçğıöşü0-9\s]", " ", t)
        hits = [m for m in known_names if m in t2]
        if not hits:
            return None
    # en uzun eşleşen
    return sorted(hits, key=len, reverse=True)[0]

def flatten(posts_with_comments: List[dict]) -> pd.DataFrame:
    """post + comments -> DataFrame: post_id, post_time, post_msg, comment_id, comment_time, author, message"""
    rows = []
    for p in posts_with_comments:
        post = p.get("post", {})
        pid = post.get("id", "")
        pmsg = post.get("message", "") or ""
        ptime = post.get("created_time", "")
        for c in p.get("comments", []):
            rows.append({
                "post_id": pid,
                "post_time": ptime,
                "post_message": pmsg,
                "comment_id": c.get("id", ""),
                "comment_time": c.get("created_time", ""),
                "author": (c.get("from") or {}).get("name", ""),
                "message": c.get("message", "") or ""
            })
    df = pd.DataFrame(rows)
    if len(df)==0:
        return pd.DataFrame(columns=["post_id","post_time","post_message","comment_id","comment_time","author","message","date"])
    # ISO -> date
    def to_date(s):
        try:
            return datetime.fromisoformat(s.replace("Z","+00:00"))
        except Exception:
            return pd.NaT
    df["date"] = df["comment_time"].apply(to_date)
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df

def summarize_by_mahalle(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("mahalle").size().reset_index(name="count")
    return g.sort_values("count", ascending=False)

def summarize_by_category(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("kategori").size().reset_index(name="count")
    return g.sort_values("count", ascending=False)
