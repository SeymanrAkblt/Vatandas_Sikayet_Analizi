import os
import requests
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# .env dosyasını yükle (main.py ile aynı klasörde olmalı)
load_dotenv()

GRAPH_BASE = "https://graph.facebook.com/v19.0"

# .env'den oku – kesinlikle hardcoded fallback kullanma
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "").strip()
PAGE_ID_OR_USERNAME = os.getenv("FACEBOOK_PAGE_ID", "").strip()  # numeric ID ya da sayfa kullanıcı adı olabilir


# --- Yardımcılar -------------------------------------------------------------

def _mask_token(tok: str) -> str:
    if not tok:
        return ""
    if len(tok) <= 10:
        return "***"
    return tok[:4] + "..." + tok[-4:]

def _is_numeric_id(s: str) -> bool:
    return s.isdigit()

def _get(url: str, params: Dict) -> Dict:
    r = requests.get(url, params=params, timeout=30)
    # 200 gelse bile Facebook JSON içinde "error" döndürebilir
    try:
        js = r.json()
        if isinstance(js, dict) and js.get("error"):
            msg = js["error"].get("message", "Graph API error")
            raise RuntimeError(msg)
    except ValueError:
        r.raise_for_status()
    r.raise_for_status()
    return r.json()

def _check_env_or_raise():
    problems = []
    if not FACEBOOK_ACCESS_TOKEN:
        problems.append("FACEBOOK_ACCESS_TOKEN boş")
    if not PAGE_ID_OR_USERNAME:
        problems.append("FACEBOOK_PAGE_ID boş")
    if problems:
        raise RuntimeError("⚠️ .env eksik: " + ", ".join(problems))

    # Basit format kontrolü
    if not (FACEBOOK_ACCESS_TOKEN.startswith("EA") and len(FACEBOOK_ACCESS_TOKEN) > 40):
        raise RuntimeError("⚠️ Token formatı şüpheli. Page Access Token kullandığından emin ol. "
                           f"Okunan: { _mask_token(FACEBOOK_ACCESS_TOKEN) }")

def resolve_page_id(page_id_or_username: str) -> str:
    """Kullanıcı adı girildiyse numeric ID'ye çevirir; zaten numeric ise aynen döner."""
    if _is_numeric_id(page_id_or_username):
        return page_id_or_username
    # Username verilmiş → id al
    url = f"{GRAPH_BASE}/{page_id_or_username}"
    params = {"access_token": FACEBOOK_ACCESS_TOKEN, "fields": "id"}
    js = _get(url, params)
    pid = js.get("id")
    if not pid or not _is_numeric_id(pid):
        raise RuntimeError("⚠️ PAGE_ID çözülemedi. Kullanıcı adı doğru mu?")
    return pid


# --- Ana işlevler ------------------------------------------------------------

def get_posts(limit: int = 25) -> List[Dict]:
    _check_env_or_raise()
    page_id = resolve_page_id(PAGE_ID_OR_USERNAME)

    fields = "id,message,created_time,permalink_url"
    params = {"access_token": FACEBOOK_ACCESS_TOKEN, "limit": limit, "fields": fields}

    # 1) /posts
    url = f"{GRAPH_BASE}/{page_id}/posts"
    js = _get(url, params)
    data = js.get("data", []) or []

    # 2) fallback: /feed
    if not data:
        url = f"{GRAPH_BASE}/{page_id}/feed"
        js = _get(url, params)
        data = js.get("data", []) or []

    # 3) fallback: /published_posts
    if not data:
        url = f"{GRAPH_BASE}/{page_id}/published_posts"
        js = _get(url, params)
        data = js.get("data", []) or []

    return data

def get_comments_for_post(post_id: str, limit: int = 100) -> List[Dict]:
    _check_env_or_raise()
    url = f"{GRAPH_BASE}/{post_id}/comments"
    params = {
        "access_token": FACEBOOK_ACCESS_TOKEN,
        "limit": limit,
        "fields": "id,message,created_time,from"
    }
    js = _get(url, params)
    return js.get("data", []) or []

def fetch_posts_with_comments(limit_posts: int = 25, limit_comments: int = 200) -> List[Dict]:
    # Küçük bir tanı bilgi: hangi ID ve token uzunluğu yüklenmiş
    print(f"[facebook] PAGE_ID/.env: '{PAGE_ID_OR_USERNAME}' | token: { _mask_token(FACEBOOK_ACCESS_TOKEN) }")

    posts = get_posts(limit_posts)
    out = []
    for p in posts:
        pid = p.get("id", "")
        cmts = []
        if pid:
            try:
                cmts = get_comments_for_post(pid, limit_comments)
            except Exception as e:
                # Her post için yorumu zorunlu kılma; post yine listelensin
                print(f"[facebook] yorum çekilemedi ({pid}): {e}")
                cmts = []
        out.append({"post": p, "comments": cmts})

    if not out:
        raise RuntimeError(
            "Hiç gönderi/yorum gelmedi.\n"
            "- Token bir 'Page Access Token' mı?\n"
            "- İzinler: pages_read_user_content, pages_read_engagement var mı?\n"
            "- PAGE_ID doğru mu (numeric ID ya da doğru kullanıcı adı)?"
        )
    return out
