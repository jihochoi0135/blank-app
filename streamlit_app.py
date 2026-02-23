import streamlit as st
import json
import re
from pathlib import Path

st.set_page_config(
    page_title="V26 구종 데이터베이스",
    page_icon="⚾",
    layout="wide",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Bebas+Neue&display=swap');

:root {
    --bg: #0d0f14;
    --surface: #161920;
    --surface2: #1e2230;
    --accent: #e84545;
    --accent2: #f5a623;
    --text: #e8eaf0;
    --muted: #5a6070;
    --border: #2a2f3d;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif;
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}

h1, h2, h3 {
    font-family: 'Bebas Neue', 'Noto Sans KR', sans-serif;
    letter-spacing: 2px;
}

.pitch-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 700;
    margin: 2px;
    letter-spacing: 0.5px;
}

.player-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}

.player-card:hover {
    border-color: var(--accent);
}

.player-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
}

.player-meta {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
}

.tag-golgl { background: #e84545; color: white; }
.tag-sig { background: #2563eb; color: white; }
.tag-impac { background: #16a34a; color: white; }
.tag-role { background: #7c3aed; color: white; }
.tag-team { background: #374151; color: #d1d5db; }

.pitch-포심 { background: #1e3a5f; color: #60a5fa; }
.pitch-투심 { background: #1e3a2f; color: #4ade80; }
.pitch-체인지업 { background: #3f1d2f; color: #f472b6; }
.pitch-서클체인지업 { background: #4a1060; color: #d946ef; }
.pitch-슬라이더 { background: #3f2c10; color: #fb923c; }
.pitch-커브 { background: #2c1c10; color: #fbbf24; }
.pitch-커터 { background: #1a2c20; color: #34d399; }
.pitch-싱커 { background: #2a1520; color: #f87171; }
.pitch-포크 { background: #1a1a2e; color: #818cf8; }
.pitch-스플리터 { background: #2d1b3d; color: #c084fc; }

.section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    letter-spacing: 3px;
    color: var(--accent);
    border-left: 4px solid var(--accent);
    padding-left: 12px;
    margin: 20px 0 12px 0;
}

.count-chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 13px;
    color: var(--muted);
    display: inline-block;
    margin-left: 8px;
}

.stTextInput > div > input, .stSelectbox > div, .stMultiSelect > div {
    background-color: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

.stButton button {
    background: var(--accent);
    color: white;
    border: none;
    font-weight: 700;
    letter-spacing: 1px;
    border-radius: 6px;
}

.stButton button:hover {
    background: #c73333;
}

hr { border-color: var(--border); }

.header-banner {
    background: linear-gradient(135deg, #0d0f14 0%, #1a1020 50%, #0d0f14 100%);
    border: 1px solid var(--border);
    border-bottom: 3px solid var(--accent);
    border-radius: 8px;
    padding: 24px 32px;
    margin-bottom: 24px;
    text-align: center;
}

.header-banner h1 {
    font-size: 48px;
    color: var(--text);
    margin: 0;
    line-height: 1;
}

.header-banner p {
    color: var(--muted);
    margin-top: 8px;
    font-size: 14px;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)

# ─── Data ─────────────────────────────────────────────────────────────────────

DATA_FILE = Path("pitcher_data.json")

PITCH_TYPES = ["포심", "투심", "체인지업", "서클체인지업", "슬라이더", "커브", "커터", "싱커", "포크", "스플리터"]

TEAMS = ["골글", "삼성", "기아", "KT", "한화", "LG", "SSG", "키움", "롯데", "NC", "두산"]

ROLES = ["선발", "중계", "마무리"]

IMPAC_TYPES = ["골", "우에", "좌에", "여사", "가사", "당쇠", "구조대", "베테랑", "국에", "탑", "구마",
               "얼리", "베포", "분메", "파볼", "저니맨", "키플", "백노", "난세", "죄에", "라이브",
               "전천후", "탑", "마무리", "FA", "올"]

def parse_year_or_impac(prefix: str):
    """Returns (year_or_none, impac_type_or_none) from prefix like '22', '84(85, 우에)', 'FA', '우에', etc."""
    if not prefix:
        return None, None
    
    # Could be like "84(85, 우에)" or "22(여사)" or "우에" or "FA" or "98" 
    # Extract all numbers
    nums = re.findall(r'\d+', prefix)
    # Extract all Korean words and known Latin tags
    korean_parts = re.findall(r'[가-힣]+', prefix)
    latin_parts = re.findall(r'[A-Za-z]+', prefix)
    
    year = int(nums[0]) if nums else None
    impac_list = korean_parts + [p for p in latin_parts if p.upper() in ['FA', 'MVP']]
    impac = impac_list[0] if impac_list else None
    
    return year, impac

def default_data():
    """Parse the hardcoded example data into structured format."""
    raw_players = [
        # 골글
        {"team": "골글", "role": "선발", "raw_prefix": "", "name": "페디", "pitches": ["체인지업", "슬라이더", "커브", "커터", "싱커"]},
        {"team": "골글", "role": "선발", "raw_prefix": "", "name": "미란다", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "골글", "role": "선발", "raw_prefix": "", "name": "폰세", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "골글", "role": "선발", "raw_prefix": "", "name": "안우진", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "골글", "role": "선발", "raw_prefix": "", "name": "구대성", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "골글", "role": "선발", "raw_prefix": "", "name": "김광현", "pitches": ["포심", "체인지업", "슬라이더", "포크", "커터"]},
        # 삼성
        {"team": "삼성", "role": "선발", "raw_prefix": "22", "name": "수아레즈", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "삼성", "role": "선발", "raw_prefix": "14", "name": "벤덴헐크", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "삼성", "role": "선발", "raw_prefix": "95", "name": "김상엽", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "삼성", "role": "선발", "raw_prefix": "우에", "name": "김시진", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "삼성", "role": "선발", "raw_prefix": "좌에", "name": "권영호", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "삼성", "role": "선발", "raw_prefix": "가사", "name": "레일런", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커터"]},
        {"team": "삼성", "role": "선발", "raw_prefix": "가사", "name": "배영수", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "10", "name": "권혁", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "가사", "name": "이호성", "pitches": ["포심", "슬라이더", "커브", "커터"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "얼리", "name": "백정현", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "당쇠", "name": "오봉옥", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "구조대", "name": "김현욱", "pitches": ["포심", "서클체인지업", "커브", "싱커"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "베테랑", "name": "곽채진", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "키플", "name": "권오준", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "여사", "name": "우규민", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "구마", "name": "심창민", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "삼성", "role": "중계", "raw_prefix": "국에", "name": "최충연", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "삼성", "role": "마무리", "raw_prefix": "여사", "name": "오승환", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        # 기아
        {"team": "기아", "role": "선발", "raw_prefix": "우에", "name": "선동열", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "기아", "role": "선발", "raw_prefix": "여사", "name": "윤석민", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "기아", "role": "선발", "raw_prefix": "죄에", "name": "양현종", "pitches": ["포심", "체인지업", "서클체인지업", "슬라이더", "커브"]},
        {"team": "기아", "role": "선발", "raw_prefix": "20", "name": "브룩스", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "기아", "role": "선발", "raw_prefix": "25", "name": "네일", "pitches": ["투심", "체인지업", "슬라이더", "커터"]},
        {"team": "기아", "role": "선발", "raw_prefix": "91", "name": "이강철", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "기아", "role": "중계", "raw_prefix": "86", "name": "김정수", "pitches": ["포심", "슬라이더", "커브", "싱커"]},
        {"team": "기아", "role": "중계", "raw_prefix": "구조대", "name": "유동훈", "pitches": ["포심", "체인지업", "커브", "싱커"]},
        {"team": "기아", "role": "중계", "raw_prefix": "00", "name": "오봉옥", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "기아", "role": "중계", "raw_prefix": "당쇠", "name": "임기영", "pitches": ["포심", "서클체인지업", "슬라이더", "싱커"]},
        {"team": "기아", "role": "중계", "raw_prefix": "당쇠", "name": "송유석", "pitches": ["포심", "투심", "슬라이더", "커브"]},
        {"team": "기아", "role": "중계", "raw_prefix": "국에", "name": "최지민", "pitches": ["포심", "체인지업", "슬라이더"]},
        {"team": "기아", "role": "마무리", "raw_prefix": "여사", "name": "한기주", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        # KT
        {"team": "KT", "role": "선발", "raw_prefix": "22", "name": "엄상백", "pitches": ["포심", "체인지업", "슬라이더"]},
        {"team": "KT", "role": "선발", "raw_prefix": "분메", "name": "쿠에바스", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커터"]},
        {"team": "KT", "role": "선발", "raw_prefix": "원투", "name": "벤릭", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "커터"]},
        {"team": "KT", "role": "선발", "raw_prefix": "우에", "name": "데스파이네", "pitches": ["포심", "투심", "체인지업", "커브", "커터"]},
        {"team": "KT", "role": "선발", "raw_prefix": "가사", "name": "소형준", "pitches": ["투심", "체인지업", "커브", "커터"]},
        {"team": "KT", "role": "선발", "raw_prefix": "우에", "name": "소형준", "pitches": ["투심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "KT", "role": "선발", "raw_prefix": "우에", "name": "고영표", "pitches": ["포심", "투심", "서클체인지업", "슬라이더", "커브"]},
        {"team": "KT", "role": "선발", "raw_prefix": "탑", "name": "고영표", "pitches": ["포심", "투심", "서클체인지업", "커브", "커터"]},
        {"team": "KT", "role": "중계", "raw_prefix": "구조대", "name": "우규민", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "KT", "role": "중계", "raw_prefix": "가사", "name": "박영현", "pitches": ["포심", "슬라이더", "커브", "커터", "스플리터"]},
        {"team": "KT", "role": "중계", "raw_prefix": "22", "name": "김민수", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "KT", "role": "중계", "raw_prefix": "15", "name": "조무근", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "KT", "role": "중계", "raw_prefix": "얼리", "name": "손동현", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "KT", "role": "중계", "raw_prefix": "가사", "name": "손동현", "pitches": ["포심", "슬라이더", "스플리터"]},
        {"team": "KT", "role": "중계", "raw_prefix": "당쇠", "name": "주권", "pitches": ["포심", "체인지업", "커브", "싱커"]},
        {"team": "KT", "role": "중계", "raw_prefix": "국에", "name": "심재민", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "KT", "role": "마무리", "raw_prefix": "구마", "name": "김재윤", "pitches": ["포심", "투심", "슬라이더", "커브", "스플리터"]},
        {"team": "KT", "role": "마무리", "raw_prefix": "마무리", "name": "김재윤", "pitches": ["포심", "슬라이더", "스플리터"]},
        {"team": "KT", "role": "마무리", "raw_prefix": "여사", "name": "박영현", "pitches": ["포심", "체인지업", "슬라이더"]},
        # 한화
        {"team": "한화", "role": "선발", "raw_prefix": "올", "name": "폰세", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "한화", "role": "선발", "raw_prefix": "FA", "name": "엄상백", "pitches": ["포심", "체인지업", "슬라이더", "커터"]},
        {"team": "한화", "role": "선발", "raw_prefix": "96", "name": "정민철", "pitches": ["포심", "슬라이더", "커브", "포크", "싱커"]},
        {"team": "한화", "role": "선발", "raw_prefix": "12", "name": "류현진", "pitches": ["포심", "체인지업", "서클체인지업", "슬라이더", "커브"]},
        {"team": "한화", "role": "선발", "raw_prefix": "여사", "name": "송진우", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "한화", "role": "중계", "raw_prefix": "가사", "name": "문동주", "pitches": ["포심", "투심", "슬라이더", "커브", "포크"]},
        {"team": "한화", "role": "중계", "raw_prefix": "여사", "name": "한승혁", "pitches": ["포심", "슬라이더", "커브", "포크", "싱커"]},
        {"team": "한화", "role": "중계", "raw_prefix": "여사", "name": "이민우", "pitches": ["포심", "투심", "슬라이더", "커브", "커터"]},
        {"team": "한화", "role": "중계", "raw_prefix": "당쇠", "name": "마정길", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "한화", "role": "중계", "raw_prefix": "당쇠", "name": "한용덕", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "한화", "role": "중계", "raw_prefix": "15", "name": "박정진", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "한화", "role": "중계", "raw_prefix": "18", "name": "이태양", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "한화", "role": "중계", "raw_prefix": "20", "name": "윤대경", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "한화", "role": "중계", "raw_prefix": "국에", "name": "김서현", "pitches": ["포심", "체인지업", "슬라이더"]},
        {"team": "한화", "role": "마무리", "raw_prefix": "가사", "name": "구대성", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        # LG
        {"team": "LG", "role": "선발", "raw_prefix": "탑", "name": "임찬규", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "LG", "role": "선발", "raw_prefix": "22", "name": "플렉슨", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "커터"]},
        {"team": "LG", "role": "선발", "raw_prefix": "13", "name": "리즈", "pitches": ["포심", "슬라이더", "커브", "포크", "커터"]},
        {"team": "LG", "role": "선발", "raw_prefix": "22", "name": "켈리", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "LG", "role": "선발", "raw_prefix": "가사", "name": "톨허스터", "pitches": ["포심", "투심", "커브", "포크", "커터"]},
        {"team": "LG", "role": "선발", "raw_prefix": "94", "name": "이상훈", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "LG", "role": "선발", "raw_prefix": "구마", "name": "윌슨", "pitches": ["포심", "투심", "체인지업", "커브", "커터"]},
        {"team": "LG", "role": "선발", "raw_prefix": "라이브", "name": "치리노스", "pitches": ["투심", "슬라이더", "포크"]},
        {"team": "LG", "role": "중계", "raw_prefix": "11", "name": "한희", "pitches": ["포심", "체인지업", "커브", "싱커"]},
        {"team": "LG", "role": "중계", "raw_prefix": "02", "name": "장문석", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "LG", "role": "중계", "raw_prefix": "여사", "name": "신윤호", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "LG", "role": "중계", "raw_prefix": "가사", "name": "에르난데스", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "LG", "role": "중계", "raw_prefix": "구마", "name": "정우영", "pitches": ["슬라이더", "포크", "커터", "싱커"]},
        {"team": "LG", "role": "중계", "raw_prefix": "전천후", "name": "우규민", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "LG", "role": "중계", "raw_prefix": "국에", "name": "유원상", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "LG", "role": "마무리", "raw_prefix": "마무리", "name": "김용수", "pitches": ["포심", "체인지업", "슬라이더", "커브", "스플리터"]},
        # SSG
        {"team": "SSG", "role": "선발", "raw_prefix": "22", "name": "김광현", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "스플리터"]},
        {"team": "SSG", "role": "선발", "raw_prefix": "08", "name": "김광현", "pitches": ["포심", "체인지업", "슬라이더", "포크", "커터"]},
        {"team": "SSG", "role": "선발", "raw_prefix": "22", "name": "폰트", "pitches": ["포심", "투심", "슬라이더", "커브"]},
        {"team": "SSG", "role": "선발", "raw_prefix": "여사", "name": "앤더슨", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "SSG", "role": "선발", "raw_prefix": "우에", "name": "켈리", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "SSG", "role": "선발", "raw_prefix": "베테랑", "name": "김원형", "pitches": ["포심", "서클체인지업", "커브", "포크", "싱커"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "구조대", "name": "조웅천", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "12", "name": "박희수", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "05", "name": "위재영", "pitches": ["포심", "투심", "슬라이더", "커브", "포크"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "24", "name": "조병현", "pitches": ["포심", "커브", "포크"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "여사", "name": "김현욱", "pitches": ["포심", "서클체인지업", "커브", "싱커"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "가사", "name": "송은범", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "백노", "name": "노경은", "pitches": ["포심", "투심", "슬라이더", "커브", "포크"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "국에", "name": "오상민", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "SSG", "role": "중계", "raw_prefix": "전천후", "name": "김원형", "pitches": ["포심", "서클체인지업", "커브", "포크", "싱커"]},
        {"team": "SSG", "role": "마무리", "raw_prefix": "07", "name": "정대현", "pitches": ["포심", "슬라이더", "커브", "싱커"]},
        # 키움
        {"team": "키움", "role": "선발", "raw_prefix": "98", "name": "김수경", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "키움", "role": "선발", "raw_prefix": "98", "name": "정명원", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "키움", "role": "선발", "raw_prefix": "22", "name": "요키시", "pitches": ["투심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "선발", "raw_prefix": "06", "name": "장원삼", "pitches": ["포심", "서클체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "선발", "raw_prefix": "우에", "name": "장명부", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "키움", "role": "선발", "raw_prefix": "우에", "name": "박정현", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "키움", "role": "선발", "raw_prefix": "난세", "name": "후라도", "pitches": ["포심", "체인지업", "커브", "커터", "싱커"]},
        {"team": "키움", "role": "선발", "raw_prefix": "죄에", "name": "최창호", "pitches": ["포심", "투심", "슬라이더", "커브", "포크"]},
        {"team": "키움", "role": "선발", "raw_prefix": "백노", "name": "나이트", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "키움", "role": "선발", "raw_prefix": "좌에", "name": "밴헤켄", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "키움", "role": "중계", "raw_prefix": "베포", "name": "한현희", "pitches": ["포심", "투심", "서클체인지업", "슬라이더"]},
        {"team": "키움", "role": "중계", "raw_prefix": "국에", "name": "한현희", "pitches": ["포심", "체인지업", "서클체인지업", "슬라이더", "싱커"]},
        {"team": "키움", "role": "중계", "raw_prefix": "14", "name": "조상우", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "중계", "raw_prefix": "구조대", "name": "조웅천", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "키움", "role": "중계", "raw_prefix": "당쇠", "name": "신완근", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "중계", "raw_prefix": "여사", "name": "김재웅", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "중계", "raw_prefix": "여사", "name": "김성민", "pitches": ["투심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "중계", "raw_prefix": "06", "name": "신철인", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "중계", "raw_prefix": "국에", "name": "조규제", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "키움", "role": "마무리", "raw_prefix": "가사", "name": "조용준", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "키움", "role": "마무리", "raw_prefix": "여사", "name": "위재영", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "키움", "role": "마무리", "raw_prefix": "06", "name": "박승민", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        # 롯데
        {"team": "롯데", "role": "선발", "raw_prefix": "파볼", "name": "박세웅", "pitches": ["포심", "슬라이더", "커브", "포크", "싱커"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "84", "name": "최동원", "pitches": ["포심", "투심", "슬라이더", "커브", "스플리터"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "우에", "name": "스트레일리", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "91", "name": "박동희", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "17", "name": "레일리", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "좌에", "name": "반즈", "pitches": ["포심", "투심", "체인지업", "슬라이더"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "백노", "name": "윌커슨", "pitches": ["포심", "체인지업", "슬라이더", "커브", "커터"]},
        {"team": "롯데", "role": "선발", "raw_prefix": "가사", "name": "염종석", "pitches": ["포심", "투심", "슬라이더", "커브", "싱커"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "여사", "name": "강영식", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "포크"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "당쇠", "name": "임경완", "pitches": ["포심", "슬라이더", "커브", "싱커"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "키플", "name": "정현수", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "구조대", "name": "박석진", "pitches": ["포심", "서클체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "22", "name": "구승민", "pitches": ["포심", "슬라이더", "포크"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "22", "name": "나균안", "pitches": ["포심", "슬라이더", "커브", "포크", "커터"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "가사", "name": "강상수", "pitches": ["포심", "체인지업", "서클체인지업", "슬라이더", "커브"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "FA", "name": "정대현", "pitches": ["포심", "슬라이더", "커브", "싱커"]},
        {"team": "롯데", "role": "중계", "raw_prefix": "국에", "name": "김진욱", "pitches": ["포심", "슬라이더", "커브"]},
        {"team": "롯데", "role": "마무리", "raw_prefix": "여사", "name": "손승락", "pitches": ["포심", "투심", "슬라이더", "커터"]},
        {"team": "롯데", "role": "마무리", "raw_prefix": "얼리", "name": "김원중", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        # NC
        {"team": "NC", "role": "선발", "raw_prefix": "우에", "name": "페디", "pitches": ["체인지업", "슬라이더", "커브", "커터", "싱커"]},
        {"team": "NC", "role": "선발", "raw_prefix": "여사", "name": "하든", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "NC", "role": "선발", "raw_prefix": "가사", "name": "찰리", "pitches": ["포심", "체인지업", "슬라이더", "커터", "싱커"]},
        {"team": "NC", "role": "선발", "raw_prefix": "20", "name": "구창모", "pitches": ["포심", "슬라이더", "커브", "스플리터"]},
        {"team": "NC", "role": "선발", "raw_prefix": "22", "name": "루친스키", "pitches": ["포심", "커브", "포크", "커터", "싱커"]},
        {"team": "NC", "role": "선발", "raw_prefix": "13", "name": "이재학", "pitches": ["포심", "체인지업", "서클체인지업", "슬라이더", "커브"]},
        {"team": "NC", "role": "중계", "raw_prefix": "당쇠", "name": "최금강", "pitches": ["포심", "투심", "슬라이더", "커브"]},
        {"team": "NC", "role": "중계", "raw_prefix": "구조대", "name": "김진성", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "NC", "role": "중계", "raw_prefix": "저니맨", "name": "임창민", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "NC", "role": "중계", "raw_prefix": "16", "name": "원종현", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "NC", "role": "중계", "raw_prefix": "23", "name": "류진욱", "pitches": ["포심", "슬라이더", "커터", "스플리터"]},
        {"team": "NC", "role": "중계", "raw_prefix": "구마", "name": "박진우", "pitches": ["포심", "투심", "체인지업", "슬라이더", "싱커"]},
        {"team": "NC", "role": "중계", "raw_prefix": "국에", "name": "이민호", "pitches": ["포심", "슬라이더", "스플리터"]},
        {"team": "NC", "role": "마무리", "raw_prefix": "22", "name": "이용찬", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "NC", "role": "마무리", "raw_prefix": "탑", "name": "류진욱", "pitches": ["포심", "슬라이더", "포크", "커터"]},
        # 두산
        {"team": "두산", "role": "선발", "raw_prefix": "좌에", "name": "미란다", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "두산", "role": "선발", "raw_prefix": "탑", "name": "잭로그", "pitches": ["포심", "체인지업", "슬라이더", "커터", "싱커"]},
        {"team": "두산", "role": "선발", "raw_prefix": "베테랑", "name": "니퍼트", "pitches": ["포심", "슬라이더", "커브", "싱커", "스플리터"]},
        {"team": "두산", "role": "선발", "raw_prefix": "19", "name": "린드블럼", "pitches": ["포심", "슬라이더", "커브", "싱커", "스플리터"]},
        {"team": "두산", "role": "선발", "raw_prefix": "우에", "name": "박철순", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "두산", "role": "선발", "raw_prefix": "04", "name": "박명환", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "두산", "role": "선발", "raw_prefix": "여사", "name": "박명환", "pitches": ["포심", "체인지업", "슬라이더", "포크", "싱커"]},
        {"team": "두산", "role": "선발", "raw_prefix": "느미", "name": "유희관", "pitches": ["포심", "체인지업", "슬라이더", "커브", "싱커"]},
        {"team": "두산", "role": "중계", "raw_prefix": "04", "name": "이재영", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "두산", "role": "중계", "raw_prefix": "중계", "name": "구자운", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "두산", "role": "중계", "raw_prefix": "12", "name": "홍상삼", "pitches": ["포심", "체인지업", "슬라이더", "커브", "포크"]},
        {"team": "두산", "role": "중계", "raw_prefix": "얼리", "name": "홍상삼", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "두산", "role": "중계", "raw_prefix": "11", "name": "정재훈", "pitches": ["포심", "체인지업", "슬라이더", "포크"]},
        {"team": "두산", "role": "중계", "raw_prefix": "구마", "name": "박치국", "pitches": ["포심", "투심", "체인지업", "슬라이더", "커브"]},
        {"team": "두산", "role": "중계", "raw_prefix": "구조대", "name": "고창성", "pitches": ["포심", "체인지업", "커브", "포크", "싱커"]},
        {"team": "두산", "role": "중계", "raw_prefix": "국에", "name": "정철원", "pitches": ["포심", "슬라이더", "커브", "스플리터"]},
        {"team": "두산", "role": "중계", "raw_prefix": "여사", "name": "김강률", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "두산", "role": "중계", "raw_prefix": "당쇠", "name": "이용호", "pitches": ["포심", "체인지업", "서클체인지업", "슬라이더", "커브"]},
        {"team": "두산", "role": "중계", "raw_prefix": "당쇠", "name": "장호연", "pitches": ["포심", "체인지업", "슬라이더", "커브", "스플리터"]},
        {"team": "두산", "role": "중계", "raw_prefix": "21", "name": "홍건희", "pitches": ["포심", "슬라이더", "커브"]},
        {"team": "두산", "role": "마무리", "raw_prefix": "가사", "name": "진필중", "pitches": ["포심", "체인지업", "슬라이더", "커브"]},
        {"team": "두산", "role": "마무리", "raw_prefix": "얼리", "name": "김택연", "pitches": ["포심", "슬라이더", "커브", "포크"]},
        {"team": "두산", "role": "마무리", "raw_prefix": "마무리", "name": "프록터", "pitches": ["포심", "투심", "체인지업", "슬라이더", "포크"]},
    ]
    
    # Classify player type
    IMPAC_KEYWORDS = {"골", "우에", "좌에", "여사", "가사", "당쇠", "구조대", "베테랑", "국에", "탑", "구마",
                      "얼리", "베포", "분메", "파볼", "저니맨", "키플", "백노", "난세", "죄에", "라이브",
                      "전천후", "마무리", "FA", "올", "중계", "원투", "느미"}
    
    for p in raw_players:
        prefix = p["raw_prefix"]
        nums = re.findall(r'\d+', prefix)
        has_num = len(nums) > 0
        
        if p["team"] == "골글":
            p["player_type"] = "골글"
            p["year"] = None
            p["impac_type"] = None
        elif has_num:
            p["player_type"] = "시그"
            p["year"] = int(nums[0])
            # check if also has impac
            korean = re.findall(r'[가-힣]+', prefix)
            p["impac_type"] = korean[0] if korean and korean[0] in IMPAC_KEYWORDS else None
        else:
            korean = re.findall(r'[가-힣A-Za-z]+', prefix)
            kw = korean[0] if korean else ""
            if kw in IMPAC_KEYWORDS or (kw.upper() in ['FA']):
                p["player_type"] = "임팩"
                p["impac_type"] = kw
                p["year"] = None
            else:
                p["player_type"] = "시그"
                p["year"] = None
                p["impac_type"] = None
    
    return raw_players

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return default_data()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── Session state ─────────────────────────────────────────────────────────────
if "players" not in st.session_state:
    st.session_state.players = load_data()

def pitch_badge(pitch):
    cls = f"pitch-{pitch}"
    return f'<span class="pitch-badge {cls}">{pitch}</span>'

def type_badge(ptype):
    cls_map = {"골글": "tag-golgl", "시그": "tag-sig", "임팩": "tag-impac"}
    return f'<span class="pitch-badge {cls_map.get(ptype, "")}">{ptype}</span>'

def player_card_html(p, idx):
    pitches_html = "".join(pitch_badge(pt) for pt in p.get("pitches", []))
    ptype = type_badge(p.get("player_type", ""))
    
    meta_parts = [f"팀: {p['team']}", f"역할: {p['role']}"]
    if p.get("year"):
        meta_parts.append(f"연도: {p['year']}")
    if p.get("impac_type"):
        meta_parts.append(f"임팩: {p['impac_type']}")
    
    meta = " · ".join(meta_parts)
    
    return f"""
    <div class="player-card">
        <div class="player-name">{p['name']} {ptype}</div>
        <div class="player-meta">{meta}</div>
        <div>{pitches_html}</div>
    </div>
    """

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;letter-spacing:3px;color:#e84545;">⚾ V26 구종 DB</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio("메뉴", ["🔍 검색", "➕ 선수 추가", "✏️ 선수 편집"], label_visibility="collapsed")

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>컴투스 프로야구 V26</h1>
    <p>⚾ 투수 구종 데이터베이스 ⚾</p>
</div>
""", unsafe_allow_html=True)

# ─── Pages ────────────────────────────────────────────────────────────────────

if "🔍 검색" in page:
    col1, col2, col3, col4 = st.columns([2,1,1,1])
    with col1:
        search_name = st.text_input("🔎 선수명 검색", placeholder="이름 입력...")
    with col2:
        filter_team = st.selectbox("팀", ["전체"] + TEAMS)
    with col3:
        filter_role = st.selectbox("역할", ["전체"] + ROLES)
    with col4:
        filter_type = st.selectbox("카드 종류", ["전체", "골글", "시그", "임팩"])
    
    col5, col6 = st.columns([2,2])
    with col5:
        filter_pitches = st.multiselect("구종 포함", PITCH_TYPES)
    with col6:
        filter_year = st.text_input("연도 (시그)", placeholder="예: 22")

    players = st.session_state.players
    filtered = players
    
    if search_name:
        filtered = [p for p in filtered if search_name in p["name"]]
    if filter_team != "전체":
        filtered = [p for p in filtered if p["team"] == filter_team]
    if filter_role != "전체":
        filtered = [p for p in filtered if p["role"] == filter_role]
    if filter_type != "전체":
        filtered = [p for p in filtered if p.get("player_type") == filter_type]
    if filter_pitches:
        filtered = [p for p in filtered if all(pt in p.get("pitches", []) for pt in filter_pitches)]
    if filter_year:
        try:
            yr = int(filter_year)
            filtered = [p for p in filtered if p.get("year") == yr]
        except:
            pass
    
    st.markdown(f'<div style="color:#5a6070;margin-bottom:16px;">검색 결과 <span style="color:#e8eaf0;font-weight:700;">{len(filtered)}</span>명</div>', unsafe_allow_html=True)
    
    # Group by team
    if filtered:
        teams_in_result = list(dict.fromkeys(p["team"] for p in filtered))
        for team in teams_in_result:
            team_players = [p for p in filtered if p["team"] == team]
            st.markdown(f'<div class="section-title">{team} <span class="count-chip">{len(team_players)}</span></div>', unsafe_allow_html=True)
            for i, p in enumerate(team_players):
                st.markdown(player_card_html(p, i), unsafe_allow_html=True)
    else:
        st.info("검색 결과가 없습니다.")

elif "➕ 선수 추가" in page:
    st.markdown('<div class="section-title">신규 선수 추가</div>', unsafe_allow_html=True)
    
    with st.form("add_player"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("선수명 *")
            team = st.selectbox("팀 *", TEAMS)
        with c2:
            role = st.selectbox("역할 *", ROLES)
            player_type = st.selectbox("카드 종류 *", ["골글", "시그", "임팩"])
        with c3:
            year = st.number_input("연도 (시그)", min_value=82, max_value=25, value=22, step=1)
            impac_type = st.selectbox("임팩 종류", ["없음"] + IMPAC_TYPES)
        
        pitches = st.multiselect("구종 *", PITCH_TYPES)
        submitted = st.form_submit_button("✅ 추가")
        
        if submitted:
            if not name or not pitches:
                st.error("선수명과 구종은 필수 입력입니다.")
            else:
                new_player = {
                    "team": team,
                    "role": role,
                    "raw_prefix": str(year) if player_type == "시그" else (impac_type if impac_type != "없음" else ""),
                    "name": name,
                    "pitches": pitches,
                    "player_type": player_type,
                    "year": year if player_type == "시그" else None,
                    "impac_type": impac_type if impac_type != "없음" else None,
                }
                st.session_state.players.append(new_player)
                save_data(st.session_state.players)
                st.success(f"✅ {name} 선수가 추가되었습니다!")

elif "✏️ 선수 편집" in page:
    st.markdown('<div class="section-title">선수 편집 / 삭제</div>', unsafe_allow_html=True)
    
    players = st.session_state.players
    
    c1, c2 = st.columns(2)
    with c1:
        search = st.text_input("선수명 검색")
    with c2:
        team_f = st.selectbox("팀 필터", ["전체"] + TEAMS)
    
    filtered = players
    if search:
        filtered = [p for p in filtered if search in p["name"]]
    if team_f != "전체":
        filtered = [p for p in filtered if p["team"] == team_f]
    
    if not filtered:
        st.info("선수를 검색하세요.")
    else:
        player_options = [f"{p['name']} ({p['team']}, {p['role']}, {p.get('player_type','')} {p.get('year','') or p.get('impac_type','') or ''})" for p in filtered]
        selected_label = st.selectbox("편집할 선수 선택", player_options)
        selected_idx_in_filtered = player_options.index(selected_label)
        selected_player = filtered[selected_idx_in_filtered]
        global_idx = players.index(selected_player)
        
        st.markdown(player_card_html(selected_player, global_idx), unsafe_allow_html=True)
        
        with st.form("edit_player"):
            c1, c2, c3 = st.columns(3)
            with c1:
                e_name = st.text_input("선수명", value=selected_player["name"])
                e_team = st.selectbox("팀", TEAMS, index=TEAMS.index(selected_player["team"]))
            with c2:
                e_role = st.selectbox("역할", ROLES, index=ROLES.index(selected_player["role"]))
                e_type = st.selectbox("카드 종류", ["골글", "시그", "임팩"], 
                    index=["골글", "시그", "임팩"].index(selected_player.get("player_type", "시그")))
            with c3:
                cur_year = selected_player.get("year") or 22
                e_year = st.number_input("연도 (시그)", min_value=82, max_value=25, value=int(cur_year))
                cur_impac = selected_player.get("impac_type") or "없음"
                opts = ["없음"] + IMPAC_TYPES
                impac_idx = opts.index(cur_impac) if cur_impac in opts else 0
                e_impac = st.selectbox("임팩 종류", opts, index=impac_idx)
            
            e_pitches = st.multiselect("구종", PITCH_TYPES, default=selected_player.get("pitches", []))
            
            c_save, c_del = st.columns(2)
            with c_save:
                save = st.form_submit_button("💾 저장")
            with c_del:
                delete = st.form_submit_button("🗑️ 삭제", type="secondary")
            
            if save:
                st.session_state.players[global_idx] = {
                    "team": e_team,
                    "role": e_role,
                    "raw_prefix": str(e_year) if e_type == "시그" else (e_impac if e_impac != "없음" else ""),
                    "name": e_name,
                    "pitches": e_pitches,
                    "player_type": e_type,
                    "year": e_year if e_type == "시그" else None,
                    "impac_type": e_impac if e_impac != "없음" else None,
                }
                save_data(st.session_state.players)
                st.success("✅ 저장되었습니다!")
                st.rerun()
            
            if delete:
                st.session_state.players.pop(global_idx)
                save_data(st.session_state.players)
                st.success("🗑️ 삭제되었습니다!")
                st.rerun()