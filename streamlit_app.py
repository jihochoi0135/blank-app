import streamlit as st
import json
import re
import base64
import requests
from pathlib import Path

st.set_page_config(page_title="V26 구종 데이터베이스", page_icon="⚾", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Bebas+Neue&display=swap');
:root {
    --bg: #0d0f14; --surface: #161920; --surface2: #1e2230;
    --accent: #e84545; --text: #e8eaf0; --muted: #5a6070; --border: #2a2f3d;
}
html, body, [data-testid="stAppViewContainer"] { background-color:var(--bg)!important; color:var(--text)!important; font-family:'Noto Sans KR',sans-serif; }
[data-testid="stSidebar"] { background-color:var(--surface)!important; border-right:1px solid var(--border); }
h1,h2,h3 { font-family:'Bebas Neue','Noto Sans KR',sans-serif; letter-spacing:2px; }
.pitch-badge { display:inline-block; padding:2px 10px; border-radius:4px; font-size:12px; font-weight:700; margin:2px; }
.player-card { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px; }
.player-card:hover { border-color:var(--accent); }
.player-name { font-size:18px; font-weight:700; color:var(--text); margin-bottom:4px; }
.player-meta { font-size:12px; color:var(--muted); margin-bottom:8px; }
.pitch-포심{background:#1e3a5f;color:#60a5fa} .pitch-투심{background:#1e3a2f;color:#4ade80}
.pitch-체인지업{background:#3f1d2f;color:#f472b6} .pitch-서클체인지업{background:#4a1060;color:#d946ef}
.pitch-슬라이더{background:#3f2c10;color:#fb923c} .pitch-커브{background:#2c1c10;color:#fbbf24}
.pitch-커터{background:#1a2c20;color:#34d399} .pitch-싱커{background:#2a1520;color:#f87171}
.pitch-포크{background:#1a1a2e;color:#818cf8} .pitch-스플리터{background:#2d1b3d;color:#c084fc}
.section-title { font-family:'Bebas Neue',sans-serif; font-size:22px; letter-spacing:3px; color:var(--accent); border-left:4px solid var(--accent); padding-left:12px; margin:20px 0 12px 0; }
.count-chip { background:var(--surface2); border:1px solid var(--border); border-radius:20px; padding:2px 12px; font-size:13px; color:var(--muted); display:inline-block; margin-left:8px; }
.stTextInput>div>input,.stSelectbox>div,.stMultiSelect>div { background-color:var(--surface2)!important; border-color:var(--border)!important; color:var(--text)!important; }
hr { border-color:var(--border); }



/* Card type colored buttons - inject via JS-based class trick not available,
   so we use streamlit's built-in primary/secondary and override colors inline */
button[data-testid*="골글"], button[data-testid*="시그"], button[data-testid*="임팩"] {
    font-weight: 700 !important;
}
.header-banner { background:linear-gradient(135deg,#0d0f14 0%,#1a1020 50%,#0d0f14 100%); border:1px solid var(--border); border-bottom:3px solid var(--accent); border-radius:8px; padding:24px 32px; margin-bottom:24px; text-align:center; }
.header-banner h1 { font-size:48px; color:var(--text); margin:0; line-height:1; }
.header-banner p { color:var(--muted); margin-top:8px; font-size:14px; letter-spacing:2px; }
.flabel { font-size:12px; color:#5a6070; letter-spacing:1px; margin-bottom:4px; margin-top:8px; }

/* Action buttons (추가/저장/삭제) - visible styled */
.action-btn > div > button { background:var(--accent)!important; color:white!important; font-weight:700!important; border:none!important; border-radius:6px!important; }
.action-btn > div > button:hover { background:#c73333!important; }
.del-btn > div > button { background:#374151!important; color:#f87171!important; font-weight:700!important; border:1px solid #f87171!important; border-radius:6px!important; }

/* Filter buttons: hide native Streamlit button text/style, show only our custom div above */
.fbtn-wrap { position:relative; }
.fbtn-wrap > div[data-testid="stButton"] > button {
    position:absolute!important; top:0!important; left:0!important;
    width:100%!important; height:100%!important;
    opacity:0!important; cursor:pointer!important;
    border:none!important; background:transparent!important;
    z-index:10!important; margin:0!important; padding:0!important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DATA_FILE = Path("pitcher_data.json")
PITCH_TYPES = ["포심","투심","체인지업","서클체인지업","슬라이더","커브","커터","싱커","포크","스플리터"]
TEAMS = ["삼성","기아","KT","한화","LG","SSG","키움","롯데","NC","두산"]
ROLES = ["선발","중계","마무리"]
IMPAC_TYPES = ["우에","좌에","여사","가사","당쇠","구조대","베테랑","탑","구마",
               "얼리","베포","분메","파볼","저니맨","키플","백노","난세","죄에",
               "전천후","마무리","FA","올","중계","느미"]
TYPE_CFG = {"골글":("#c9a227","black"), "시그":("#dc2626","white"), "임팩":("#16a34a","white"), "국대":("#2563eb","white"), "라이브":("#e8eaf0","black")}

# ── Data ───────────────────────────────────────────────────────────────────────
def default_data():
    raw = [
        {"team":"삼성","role":"선발","raw_prefix":"22","name":"수아레즈","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"선발","raw_prefix":"14","name":"벤덴헐크","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"선발","raw_prefix":"95","name":"김상엽","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"선발","raw_prefix":"우에","name":"김시진","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"선발","raw_prefix":"좌에","name":"권영호","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"삼성","role":"선발","raw_prefix":"가사","name":"레일런","pitches":["포심","투심","체인지업","슬라이더","커터"]},
        {"team":"삼성","role":"선발","raw_prefix":"가사","name":"배영수","pitches":["포심","체인지업","슬라이더","포크"]},
        # 골글 → 삼성
        {"team":"삼성","role":"선발","raw_prefix":"골","name":"페디","pitches":["체인지업","슬라이더","커브","커터","싱커"]},
        {"team":"삼성","role":"선발","raw_prefix":"골","name":"미란다","pitches":["포심","체인지업","슬라이더","포크"]},
        {"team":"삼성","role":"선발","raw_prefix":"골","name":"폰세","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"삼성","role":"선발","raw_prefix":"골","name":"안우진","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"선발","raw_prefix":"골","name":"구대성","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"삼성","role":"선발","raw_prefix":"골","name":"김광현","pitches":["포심","체인지업","슬라이더","포크","커터"]},
        {"team":"삼성","role":"중계","raw_prefix":"10","name":"권혁","pitches":["포심","체인지업","슬라이더","포크"]},
        {"team":"삼성","role":"중계","raw_prefix":"가사","name":"이호성","pitches":["포심","슬라이더","커브","커터"]},
        {"team":"삼성","role":"중계","raw_prefix":"얼리","name":"백정현","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"삼성","role":"중계","raw_prefix":"당쇠","name":"오봉옥","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"중계","raw_prefix":"구조대","name":"김현욱","pitches":["포심","서클체인지업","커브","싱커"]},
        {"team":"삼성","role":"중계","raw_prefix":"베테랑","name":"곽채진","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"삼성","role":"중계","raw_prefix":"키플","name":"권오준","pitches":["포심","서클체인지업","슬라이더","커브","싱커"]},
        {"team":"삼성","role":"중계","raw_prefix":"여사","name":"우규민","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"삼성","role":"중계","raw_prefix":"구마","name":"심창민","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"삼성","role":"중계","raw_prefix":"국대","name":"최충연","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"삼성","role":"마무리","raw_prefix":"여사","name":"오승환","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"기아","role":"선발","raw_prefix":"우에","name":"선동열","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"기아","role":"선발","raw_prefix":"여사","name":"윤석민","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"기아","role":"선발","raw_prefix":"죄에","name":"양현종","pitches":["포심","체인지업","서클체인지업","슬라이더","커브"]},
        {"team":"기아","role":"선발","raw_prefix":"20","name":"브룩스","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"기아","role":"선발","raw_prefix":"25","name":"네일","pitches":["투심","체인지업","슬라이더","커터"]},
        {"team":"기아","role":"선발","raw_prefix":"91","name":"이강철","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"기아","role":"중계","raw_prefix":"86","name":"김정수","pitches":["포심","슬라이더","커브","싱커"]},
        {"team":"기아","role":"중계","raw_prefix":"구조대","name":"유동훈","pitches":["포심","체인지업","커브","싱커"]},
        {"team":"기아","role":"중계","raw_prefix":"00","name":"오봉옥","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"기아","role":"중계","raw_prefix":"당쇠","name":"임기영","pitches":["포심","서클체인지업","슬라이더","싱커"]},
        {"team":"기아","role":"중계","raw_prefix":"당쇠","name":"송유석","pitches":["포심","투심","슬라이더","커브"]},
        {"team":"기아","role":"중계","raw_prefix":"국대","name":"최지민","pitches":["포심","체인지업","슬라이더"]},
        {"team":"기아","role":"마무리","raw_prefix":"여사","name":"한기주","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"KT","role":"선발","raw_prefix":"22","name":"엄상백","pitches":["포심","체인지업","슬라이더"]},
        {"team":"KT","role":"선발","raw_prefix":"분메","name":"쿠에바스","pitches":["포심","투심","체인지업","슬라이더","커터"]},
        {"team":"KT","role":"선발","raw_prefix":"원투","name":"벤릭","pitches":["포심","서클체인지업","슬라이더","커브","커터"]},
        {"team":"KT","role":"선발","raw_prefix":"우에","name":"데스파이네","pitches":["포심","투심","체인지업","커브","커터"]},
        {"team":"KT","role":"선발","raw_prefix":"가사","name":"소형준","pitches":["투심","체인지업","커브","커터"]},
        {"team":"KT","role":"선발","raw_prefix":"우에","name":"소형준","pitches":["투심","체인지업","슬라이더","커브","커터"]},
        {"team":"KT","role":"선발","raw_prefix":"우에","name":"고영표","pitches":["포심","투심","서클체인지업","슬라이더","커브"]},
        {"team":"KT","role":"선발","raw_prefix":"탑","name":"고영표","pitches":["포심","투심","서클체인지업","커브","커터"]},
        {"team":"KT","role":"중계","raw_prefix":"구조대","name":"우규민","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"KT","role":"중계","raw_prefix":"가사","name":"박영현","pitches":["포심","슬라이더","커브","커터","스플리터"]},
        {"team":"KT","role":"중계","raw_prefix":"22","name":"김민수","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"KT","role":"중계","raw_prefix":"15","name":"조무근","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"KT","role":"중계","raw_prefix":"얼리","name":"손동현","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"KT","role":"중계","raw_prefix":"가사","name":"손동현","pitches":["포심","슬라이더","스플리터"]},
        {"team":"KT","role":"중계","raw_prefix":"당쇠","name":"주권","pitches":["포심","체인지업","커브","싱커"]},
        {"team":"KT","role":"중계","raw_prefix":"국대","name":"심재민","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"KT","role":"마무리","raw_prefix":"구마","name":"김재윤","pitches":["포심","투심","슬라이더","커브","스플리터"]},
        {"team":"KT","role":"마무리","raw_prefix":"마무리","name":"김재윤","pitches":["포심","슬라이더","스플리터"]},
        {"team":"KT","role":"마무리","raw_prefix":"여사","name":"박영현","pitches":["포심","체인지업","슬라이더"]},
        {"team":"한화","role":"선발","raw_prefix":"올","name":"폰세","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"한화","role":"선발","raw_prefix":"FA","name":"엄상백","pitches":["포심","체인지업","슬라이더","커터"]},
        {"team":"한화","role":"선발","raw_prefix":"96","name":"정민철","pitches":["포심","슬라이더","커브","포크","싱커"]},
        {"team":"한화","role":"선발","raw_prefix":"12","name":"류현진","pitches":["포심","체인지업","서클체인지업","슬라이더","커브"]},
        {"team":"한화","role":"선발","raw_prefix":"여사","name":"송진우","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"한화","role":"중계","raw_prefix":"가사","name":"문동주","pitches":["포심","투심","슬라이더","커브","포크"]},
        {"team":"한화","role":"중계","raw_prefix":"여사","name":"한승혁","pitches":["포심","슬라이더","커브","포크","싱커"]},
        {"team":"한화","role":"중계","raw_prefix":"여사","name":"이민우","pitches":["포심","투심","슬라이더","커브","커터"]},
        {"team":"한화","role":"중계","raw_prefix":"당쇠","name":"마정길","pitches":["포심","서클체인지업","슬라이더","커브","싱커"]},
        {"team":"한화","role":"중계","raw_prefix":"당쇠","name":"한용덕","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"한화","role":"중계","raw_prefix":"15","name":"박정진","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"한화","role":"중계","raw_prefix":"18","name":"이태양","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"한화","role":"중계","raw_prefix":"20","name":"윤대경","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"한화","role":"중계","raw_prefix":"국대","name":"김서현","pitches":["포심","체인지업","슬라이더"]},
        {"team":"한화","role":"마무리","raw_prefix":"가사","name":"구대성","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"LG","role":"선발","raw_prefix":"탑","name":"임찬규","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"LG","role":"선발","raw_prefix":"22","name":"플렉슨","pitches":["포심","서클체인지업","슬라이더","커브","커터"]},
        {"team":"LG","role":"선발","raw_prefix":"13","name":"리즈","pitches":["포심","슬라이더","커브","포크","커터"]},
        {"team":"LG","role":"선발","raw_prefix":"22","name":"켈리","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"LG","role":"선발","raw_prefix":"가사","name":"톨허스터","pitches":["포심","투심","커브","포크","커터"]},
        {"team":"LG","role":"선발","raw_prefix":"94","name":"이상훈","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"LG","role":"선발","raw_prefix":"구마","name":"윌슨","pitches":["포심","투심","체인지업","커브","커터"]},
        {"team":"LG","role":"선발","raw_prefix":"라이브","name":"치리노스","pitches":["투심","슬라이더","포크"]},
        {"team":"LG","role":"중계","raw_prefix":"11","name":"한희","pitches":["포심","체인지업","커브","싱커"]},
        {"team":"LG","role":"중계","raw_prefix":"02","name":"장문석","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"LG","role":"중계","raw_prefix":"여사","name":"신윤호","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"LG","role":"중계","raw_prefix":"가사","name":"에르난데스","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"LG","role":"중계","raw_prefix":"구마","name":"정우영","pitches":["슬라이더","포크","커터","싱커"]},
        {"team":"LG","role":"중계","raw_prefix":"전천후","name":"우규민","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"LG","role":"중계","raw_prefix":"국대","name":"유원상","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"LG","role":"마무리","raw_prefix":"마무리","name":"김용수","pitches":["포심","체인지업","슬라이더","커브","스플리터"]},
        {"team":"SSG","role":"선발","raw_prefix":"22","name":"김광현","pitches":["포심","서클체인지업","슬라이더","커브","스플리터"]},
        {"team":"SSG","role":"선발","raw_prefix":"08","name":"김광현","pitches":["포심","체인지업","슬라이더","포크","커터"]},
        {"team":"SSG","role":"선발","raw_prefix":"22","name":"폰트","pitches":["포심","투심","슬라이더","커브"]},
        {"team":"SSG","role":"선발","raw_prefix":"여사","name":"앤더슨","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"SSG","role":"선발","raw_prefix":"우에","name":"켈리","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"SSG","role":"선발","raw_prefix":"베테랑","name":"김원형","pitches":["포심","서클체인지업","커브","포크","싱커"]},
        {"team":"SSG","role":"중계","raw_prefix":"구조대","name":"조웅천","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"SSG","role":"중계","raw_prefix":"12","name":"박희수","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"SSG","role":"중계","raw_prefix":"05","name":"위재영","pitches":["포심","투심","슬라이더","커브","포크"]},
        {"team":"SSG","role":"중계","raw_prefix":"24","name":"조병현","pitches":["포심","커브","포크"]},
        {"team":"SSG","role":"중계","raw_prefix":"여사","name":"김현욱","pitches":["포심","서클체인지업","커브","싱커"]},
        {"team":"SSG","role":"중계","raw_prefix":"가사","name":"송은범","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"SSG","role":"중계","raw_prefix":"백노","name":"노경은","pitches":["포심","투심","슬라이더","커브","포크"]},
        {"team":"SSG","role":"중계","raw_prefix":"국대","name":"오상민","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"SSG","role":"중계","raw_prefix":"전천후","name":"김원형","pitches":["포심","서클체인지업","커브","포크","싱커"]},
        {"team":"SSG","role":"마무리","raw_prefix":"07","name":"정대현","pitches":["포심","슬라이더","커브","싱커"]},
        {"team":"키움","role":"선발","raw_prefix":"98","name":"김수경","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"키움","role":"선발","raw_prefix":"98","name":"정명원","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"키움","role":"선발","raw_prefix":"22","name":"요키시","pitches":["투심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"선발","raw_prefix":"06","name":"장원삼","pitches":["포심","서클체인지업","슬라이더","커브"]},
        {"team":"키움","role":"선발","raw_prefix":"우에","name":"장명부","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"키움","role":"선발","raw_prefix":"우에","name":"박정현","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"키움","role":"선발","raw_prefix":"난세","name":"후라도","pitches":["포심","체인지업","커브","커터","싱커"]},
        {"team":"키움","role":"선발","raw_prefix":"죄에","name":"최창호","pitches":["포심","투심","슬라이더","커브","포크"]},
        {"team":"키움","role":"선발","raw_prefix":"백노","name":"나이트","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"키움","role":"선발","raw_prefix":"좌에","name":"밴헤켄","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"키움","role":"중계","raw_prefix":"베포","name":"한현희","pitches":["포심","투심","서클체인지업","슬라이더"]},
        {"team":"키움","role":"중계","raw_prefix":"국대","name":"한현희","pitches":["포심","체인지업","서클체인지업","슬라이더","싱커"]},
        {"team":"키움","role":"중계","raw_prefix":"14","name":"조상우","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"중계","raw_prefix":"구조대","name":"조웅천","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"키움","role":"중계","raw_prefix":"당쇠","name":"신완근","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"중계","raw_prefix":"여사","name":"김재웅","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"중계","raw_prefix":"여사","name":"김성민","pitches":["투심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"중계","raw_prefix":"06","name":"신철인","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"중계","raw_prefix":"국대","name":"조규제","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"키움","role":"마무리","raw_prefix":"가사","name":"조용준","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"키움","role":"마무리","raw_prefix":"여사","name":"위재영","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"키움","role":"마무리","raw_prefix":"06","name":"박승민","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"선발","raw_prefix":"파볼","name":"박세웅","pitches":["포심","슬라이더","커브","포크","싱커"]},
        {"team":"롯데","role":"선발","raw_prefix":"84","name":"최동원","pitches":["포심","투심","슬라이더","커브","스플리터"]},
        {"team":"롯데","role":"선발","raw_prefix":"우에","name":"스트레일리","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"선발","raw_prefix":"91","name":"박동희","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"롯데","role":"선발","raw_prefix":"17","name":"레일리","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"선발","raw_prefix":"좌에","name":"반즈","pitches":["포심","투심","체인지업","슬라이더"]},
        {"team":"롯데","role":"선발","raw_prefix":"백노","name":"윌커슨","pitches":["포심","체인지업","슬라이더","커브","커터"]},
        {"team":"롯데","role":"선발","raw_prefix":"가사","name":"염종석","pitches":["포심","투심","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"중계","raw_prefix":"여사","name":"강영식","pitches":["포심","서클체인지업","슬라이더","커브","포크"]},
        {"team":"롯데","role":"중계","raw_prefix":"당쇠","name":"임경완","pitches":["포심","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"중계","raw_prefix":"키플","name":"정현수","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"롯데","role":"중계","raw_prefix":"구조대","name":"박석진","pitches":["포심","서클체인지업","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"중계","raw_prefix":"22","name":"구승민","pitches":["포심","슬라이더","포크"]},
        {"team":"롯데","role":"중계","raw_prefix":"22","name":"나균안","pitches":["포심","슬라이더","커브","포크","커터"]},
        {"team":"롯데","role":"중계","raw_prefix":"가사","name":"강상수","pitches":["포심","체인지업","서클체인지업","슬라이더","커브"]},
        {"team":"롯데","role":"중계","raw_prefix":"FA","name":"정대현","pitches":["포심","슬라이더","커브","싱커"]},
        {"team":"롯데","role":"중계","raw_prefix":"국대","name":"김진욱","pitches":["포심","슬라이더","커브"]},
        {"team":"롯데","role":"마무리","raw_prefix":"여사","name":"손승락","pitches":["포심","투심","슬라이더","커터"]},
        {"team":"롯데","role":"마무리","raw_prefix":"얼리","name":"김원중","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"NC","role":"선발","raw_prefix":"우에","name":"페디","pitches":["체인지업","슬라이더","커브","커터","싱커"]},
        {"team":"NC","role":"선발","raw_prefix":"여사","name":"하든","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"NC","role":"선발","raw_prefix":"가사","name":"찰리","pitches":["포심","체인지업","슬라이더","커터","싱커"]},
        {"team":"NC","role":"선발","raw_prefix":"20","name":"구창모","pitches":["포심","슬라이더","커브","스플리터"]},
        {"team":"NC","role":"선발","raw_prefix":"22","name":"루친스키","pitches":["포심","커브","포크","커터","싱커"]},
        {"team":"NC","role":"선발","raw_prefix":"13","name":"이재학","pitches":["포심","체인지업","서클체인지업","슬라이더","커브"]},
        {"team":"NC","role":"중계","raw_prefix":"당쇠","name":"최금강","pitches":["포심","투심","슬라이더","커브"]},
        {"team":"NC","role":"중계","raw_prefix":"구조대","name":"김진성","pitches":["포심","체인지업","슬라이더","포크"]},
        {"team":"NC","role":"중계","raw_prefix":"저니맨","name":"임창민","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"NC","role":"중계","raw_prefix":"16","name":"원종현","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"NC","role":"중계","raw_prefix":"23","name":"류진욱","pitches":["포심","슬라이더","커터","스플리터"]},
        {"team":"NC","role":"중계","raw_prefix":"구마","name":"박진우","pitches":["포심","투심","체인지업","슬라이더","싱커"]},
        {"team":"NC","role":"중계","raw_prefix":"국대","name":"이민호","pitches":["포심","슬라이더","스플리터"]},
        {"team":"NC","role":"마무리","raw_prefix":"22","name":"이용찬","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"NC","role":"마무리","raw_prefix":"탑","name":"류진욱","pitches":["포심","슬라이더","포크","커터"]},
        {"team":"두산","role":"선발","raw_prefix":"좌에","name":"미란다","pitches":["포심","체인지업","슬라이더","포크"]},
        {"team":"두산","role":"선발","raw_prefix":"탑","name":"잭로그","pitches":["포심","체인지업","슬라이더","커터","싱커"]},
        {"team":"두산","role":"선발","raw_prefix":"베테랑","name":"니퍼트","pitches":["포심","슬라이더","커브","싱커","스플리터"]},
        {"team":"두산","role":"선발","raw_prefix":"19","name":"린드블럼","pitches":["포심","슬라이더","커브","싱커","스플리터"]},
        {"team":"두산","role":"선발","raw_prefix":"우에","name":"박철순","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"두산","role":"선발","raw_prefix":"04","name":"박명환","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"두산","role":"선발","raw_prefix":"여사","name":"박명환","pitches":["포심","체인지업","슬라이더","포크","싱커"]},
        {"team":"두산","role":"선발","raw_prefix":"느미","name":"유희관","pitches":["포심","체인지업","슬라이더","커브","싱커"]},
        {"team":"두산","role":"중계","raw_prefix":"04","name":"이재영","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"두산","role":"중계","raw_prefix":"중계","name":"구자운","pitches":["포심","체인지업","슬라이더","포크"]},
        {"team":"두산","role":"중계","raw_prefix":"12","name":"홍상삼","pitches":["포심","체인지업","슬라이더","커브","포크"]},
        {"team":"두산","role":"중계","raw_prefix":"얼리","name":"홍상삼","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"두산","role":"중계","raw_prefix":"11","name":"정재훈","pitches":["포심","체인지업","슬라이더","포크"]},
        {"team":"두산","role":"중계","raw_prefix":"구마","name":"박치국","pitches":["포심","투심","체인지업","슬라이더","커브"]},
        {"team":"두산","role":"중계","raw_prefix":"구조대","name":"고창성","pitches":["포심","체인지업","커브","포크","싱커"]},
        {"team":"두산","role":"중계","raw_prefix":"국대","name":"정철원","pitches":["포심","슬라이더","커브","스플리터"]},
        {"team":"두산","role":"중계","raw_prefix":"여사","name":"김강률","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"두산","role":"중계","raw_prefix":"당쇠","name":"이용호","pitches":["포심","체인지업","서클체인지업","슬라이더","커브"]},
        {"team":"두산","role":"중계","raw_prefix":"당쇠","name":"장호연","pitches":["포심","체인지업","슬라이더","커브","스플리터"]},
        {"team":"두산","role":"중계","raw_prefix":"21","name":"홍건희","pitches":["포심","슬라이더","커브"]},
        {"team":"두산","role":"마무리","raw_prefix":"가사","name":"진필중","pitches":["포심","체인지업","슬라이더","커브"]},
        {"team":"두산","role":"마무리","raw_prefix":"얼리","name":"김택연","pitches":["포심","슬라이더","커브","포크"]},
        {"team":"두산","role":"마무리","raw_prefix":"마무리","name":"프록터","pitches":["포심","투심","체인지업","슬라이더","포크"]},
    ]
    IMPAC_KW = set(IMPAC_TYPES) | {"FA","골"}
    for p in raw:
        prefix = p["raw_prefix"]
        nums = re.findall(r'\d+', prefix)
        korean = re.findall(r'[가-힣]+', prefix)
        latin = re.findall(r'[A-Za-z]+', prefix)
        kw = (korean or latin or [""])[0]
        if prefix == "골":
            p["player_type"] = "골글"; p["year"] = None; p["impac_type"] = None
        elif kw == "국대":
            p["player_type"] = "국대"; p["year"] = None; p["impac_type"] = None
        elif kw == "라이브":
            p["player_type"] = "라이브"; p["year"] = None; p["impac_type"] = None
        elif nums:
            p["player_type"] = "시그"; p["year"] = nums[0]
            p["impac_type"] = korean[0] if korean and korean[0] in IMPAC_KW else None
        elif kw in IMPAC_KW or kw.upper() in ["FA"]:
            p["player_type"] = "임팩"; p["impac_type"] = kw; p["year"] = None
        else:
            p["player_type"] = "시그"; p["year"] = None; p["impac_type"] = None
    return raw

def _gh_cfg():
    """Return (token, gist_id) from st.secrets or (None, None)."""
    try:
        cfg = st.secrets["github"]
        return cfg["token"], cfg["gist_id"]
    except Exception:
        return None, None

def _migrate(data):
    for p in data:
        if p.get("team") == "골글":
            p["team"] = "삼성"
            p["player_type"] = "골글"
        # Convert 국에 impac → 국대 card type
        if p.get("impac_type") == "국에" or p.get("player_type") == "임팩" and p.get("impac_type") == "국에":
            p["player_type"] = "국대"
            p["impac_type"] = None
        # Convert 라이브 impac → 라이브 card type
        if p.get("impac_type") == "라이브":
            p["player_type"] = "라이브"
            p["impac_type"] = None
    return data

def save_data(data):
    token, gist_id = _gh_cfg()

    # ── Gist save ──
    if token and gist_id:
        url = f"https://api.github.com/gists/{gist_id}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        r = requests.patch(url, headers=headers, json={"files": {"pitcher_data.json": {"content": payload}}})
        if r.status_code == 200:
            return  # success

    # ── Local fallback ──
    for path in [DATA_FILE, Path("/tmp/pitcher_data.json")]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return
        except Exception:
            continue

def load_data():
    token, gist_id = _gh_cfg()

    # ── Gist load ──
    if token and gist_id:
        url = f"https://api.github.com/gists/{gist_id}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            try:
                raw = r.json()["files"]["pitcher_data.json"]["content"]
                data = json.loads(raw)
                if data:  # non-empty → migrate and return
                    return _migrate(data)
            except Exception:
                pass

    # ── Local fallback ──
    for path in [Path("/tmp/pitcher_data.json"), DATA_FILE]:
        if path.exists():
            try:
                with open(path) as f:
                    return _migrate(json.load(f))
            except Exception:
                continue
    return default_data()

if "players" not in st.session_state:
    st.session_state.players = load_data()

# ── Badge helpers ──────────────────────────────────────────────────────────────
def pitch_badge(pitch):
    return f'<span class="pitch-badge pitch-{pitch}">{pitch}</span>'

def player_card_html(p):
    ordered = sorted(p.get("pitches", []), key=lambda x: PITCH_TYPES.index(x) if x in PITCH_TYPES else 99)
    pitches_html = "".join(pitch_badge(pt) for pt in ordered)
    ptype = p.get("player_type","")
    bg, fg = TYPE_CFG.get(ptype, ("#374151","#d1d5db"))
    type_b = f'<span class="pitch-badge" style="background:{bg};color:{fg};">{ptype}</span>'
    extra = ""
    if p.get("year"):
        extra += f'<span class="pitch-badge" style="background:#1e3a5f;color:#60a5fa;">{p["year"]}</span>'
    if p.get("impac_type"):
        extra += f'<span class="pitch-badge" style="background:#16a34a;color:white;">{p["impac_type"]}</span>'
    meta = f'팀: {p["team"]} · 역할: {p["role"]}'
    return f"""<div class="player-card">
        <div class="player-name">{p['name']}</div>
        <div style="margin:6px 0">{type_b}{extra}</div>
        <div class="player-meta" style="margin-bottom:8px">{meta}</div>
        <div>{pitches_html}</div>
    </div>"""

# ── Filter button renderer (NO overlay div — pure Streamlit buttons with st.markdown label above) ──
def fbtn_row(label, options, state_key, multi=False, col_count=None, colors=None):
    st.markdown(f'<div class="flabel">{label}</div>', unsafe_allow_html=True)
    n = col_count or len(options)
    chunks = [options[i:i+n] for i in range(0, len(options), n)]
    for chunk in chunks:
        cols = st.columns(n)
        for j in range(n):
            if j >= len(chunk):
                break
            opt = chunk[j]
            s = st.session_state[state_key]
            active = (opt in s) if multi else (s == opt)
            ac = (colors or {}).get(opt, ("#e84545","white"))
            bg = ac[0] if active else "#1e2230"
            fg = ac[1] if active else "#9aa0b0"
            bdr = f"2px solid {ac[0]}" if active else "1px solid #2a2f3d"
            with cols[j]:
                # Single styled button — no overlay
                clicked = st.button(
                    opt,
                    key=f"{state_key}__{opt}",
                    use_container_width=True,
                )
                # Apply style via markdown targeting the button above
                st.markdown(f"""<style>
                div[data-testid="stButton"]:has(button[kind][data-testid]) {{}}
                </style>""", unsafe_allow_html=True)
                if clicked:
                    if multi:
                        cur = st.session_state[state_key]
                        cur.discard(opt) if opt in cur else cur.add(opt)
                        st.session_state[state_key] = cur
                    else:
                        st.session_state[state_key] = "" if s == opt else opt
                    st.rerun()
                # Show colored indicator below button
                st.markdown(
                    f'<div style="height:4px;border-radius:2px;background:{bg};margin-top:-8px;margin-bottom:4px;border:none;"></div>',
                    unsafe_allow_html=True
                )

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;letter-spacing:3px;color:#e84545;">⚾ V26 구종 DB</div>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("메뉴", ["🔍 검색", "➕ 선수 추가", "✏️ 선수 편집"])

st.markdown("""<div class="header-banner"><h1>컴투스 프로야구 V26</h1><p>⚾ 투수 구종 데이터베이스 ⚾</p></div>""", unsafe_allow_html=True)

# ── Pages ──────────────────────────────────────────────────────────────────────

def card_type_row(label, state_key, key_prefix, impac_reset_key=None):
    """Card type: button + colored underline bar. Works for search (set) and add/edit (str)."""
    st.markdown(f'<div class="flabel">{label}</div>', unsafe_allow_html=True)
    cols = st.columns(len(TYPE_CFG))
    for i, (opt, (ac, tc)) in enumerate(TYPE_CFG.items()):
        is_active = (opt in st.session_state[state_key]) if isinstance(st.session_state[state_key], set) else (st.session_state[state_key] == opt)
        with cols[i]:
            if st.button(opt, key=f"{key_prefix}_type__{opt}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                if isinstance(st.session_state[state_key], set):
                    s = st.session_state[state_key]
                    s.discard(opt) if opt in s else s.add(opt)
                    st.session_state[state_key] = s
                    if impac_reset_key and opt == "임팩" and "임팩" not in st.session_state[state_key]:
                        st.session_state[impac_reset_key] = set()
                else:
                    st.session_state[state_key] = "" if is_active else opt
                st.rerun()
            bar_color = ac if is_active else "transparent"
            st.markdown(f'<div style="height:3px;background:{bar_color};border-radius:2px;margin-top:-8px;margin-bottom:4px;"></div>', unsafe_allow_html=True)

if "🔍 검색" in page:
    for k,d in [("s_team",set()),("s_role",set()),("s_type",set()),("s_impac",set())]:
        if k not in st.session_state: st.session_state[k] = d
    if "s_sort" not in st.session_state: st.session_state["s_sort"] = "팀순"

    def s_toggle(key, val):
        s = st.session_state[key]
        s.discard(val) if val in s else s.add(val)
        st.session_state[key] = s

    def flex_btn_row(label, options, state_key, multi=True, key_prefix=None):
        """Render buttons 3–10 per row, active = primary (red), inactive = secondary."""
        st.markdown(f'<div class="flabel">{label}</div>', unsafe_allow_html=True)
        kp = key_prefix or state_key
        n = min(10, max(3, len(options)))
        chunks = [options[i:i+n] for i in range(0, len(options), n)]
        for chunk in chunks:
            cols = st.columns(len(chunk))
            for j, opt in enumerate(chunk):
                s = st.session_state[state_key]
                active = (opt in s) if multi else (s == opt)
                with cols[j]:
                    if st.button(opt, key=f"{kp}__{opt}", use_container_width=True,
                                 type="primary" if active else "secondary"):
                        if multi: s_toggle(state_key, opt)
                        else: st.session_state[state_key] = "" if active else opt
                        st.rerun()

    search_name = st.text_input("🔎 선수명 검색", placeholder="이름 입력...")
    st.markdown("---")

    flex_btn_row("팀", TEAMS, "s_team")
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    flex_btn_row("역할", ROLES, "s_role")
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    card_type_row("카드 종류", "s_type", "s", impac_reset_key="s_impac")
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    # Only show impac filter if 임팩 is selected (or nothing selected)
    show_impac = not st.session_state["s_type"] or "임팩" in st.session_state["s_type"]
    if show_impac:
        flex_btn_row("임팩 종류", IMPAC_TYPES, "s_impac")
        st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)
    elif st.session_state["s_impac"]:
        st.session_state["s_impac"] = set()

    col5, col6 = st.columns([2,1])
    with col5:
        filter_pitches = st.multiselect("구종 포함", PITCH_TYPES)
    with col6:
        filter_year = st.text_input("연도", placeholder="예: 22")

    # Sort order
    st.markdown('<div class="flabel">정렬 순서</div>', unsafe_allow_html=True)
    sort_opts = ["팀순", "이름순", "카드종류순", "역할순"]
    scols = st.columns(len(sort_opts))
    for i, opt in enumerate(sort_opts):
        active = st.session_state["s_sort"] == opt
        with scols[i]:
            if st.button(opt, key=f"s_sort__{opt}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state["s_sort"] = opt; st.rerun()

    st.markdown("---")

    # Filter
    players = st.session_state.players
    filtered = list(players)
    if search_name:
        filtered = [p for p in filtered if search_name in p["name"]]
    if st.session_state["s_team"]:
        filtered = [p for p in filtered if p["team"] in st.session_state["s_team"]]
    if st.session_state["s_role"]:
        filtered = [p for p in filtered if p["role"] in st.session_state["s_role"]]
    if st.session_state["s_type"]:
        filtered = [p for p in filtered if p.get("player_type") in st.session_state["s_type"]]
    if st.session_state["s_impac"]:
        filtered = [p for p in filtered if p.get("impac_type") in st.session_state["s_impac"]]
    if filter_pitches:
        filtered = [p for p in filtered if all(pt in p.get("pitches",[]) for pt in filter_pitches)]
    if filter_year.strip():
        filtered = [p for p in filtered if str(p.get("year") or "") == filter_year.strip()]

    # Sort
    TEAM_ORDER = {t:i for i,t in enumerate(TEAMS)}
    ROLE_ORDER = {"선발":0,"중계":1,"마무리":2}
    TYPE_ORDER = {"골글":0,"시그":1,"임팩":2}
    sort_key = st.session_state["s_sort"]
    if sort_key == "팀순":
        filtered.sort(key=lambda p: (TEAM_ORDER.get(p["team"],99), ROLE_ORDER.get(p["role"],99)))
    elif sort_key == "이름순":
        filtered.sort(key=lambda p: p["name"])
    elif sort_key == "카드종류순":
        filtered.sort(key=lambda p: (TYPE_ORDER.get(p.get("player_type",""),99), TEAM_ORDER.get(p["team"],99)))
    elif sort_key == "역할순":
        filtered.sort(key=lambda p: (ROLE_ORDER.get(p["role"],99), TEAM_ORDER.get(p["team"],99)))

    st.markdown(f'<div style="color:#5a6070;margin-bottom:16px;">검색 결과 <span style="color:#e8eaf0;font-weight:700;">{len(filtered)}</span>명</div>', unsafe_allow_html=True)

    if filtered:
        if sort_key == "팀순":
            for team in list(dict.fromkeys(p["team"] for p in filtered)):
                tp = [p for p in filtered if p["team"] == team]
                st.markdown(f'<div class="section-title">{team} <span class="count-chip">{len(tp)}</span></div>', unsafe_allow_html=True)
                for p in tp:
                    st.markdown(player_card_html(p), unsafe_allow_html=True)
        else:
            for p in filtered:
                st.markdown(player_card_html(p), unsafe_allow_html=True)
    else:
        st.info("검색 결과가 없습니다.")

elif "➕ 선수 추가" in page:
    st.markdown('<div class="section-title">신규 선수 추가</div>', unsafe_allow_html=True)

    for k,d in [("a_team",""),("a_role",""),("a_type",""),("a_impac",""),("a_pitches",set())]:
        if k not in st.session_state: st.session_state[k] = d

    def a_toggle_single(key, val):
        st.session_state[key] = "" if st.session_state[key] == val else val
    def a_toggle_multi(key, val):
        s = st.session_state[key]
        s.discard(val) if val in s else s.add(val)
        st.session_state[key] = s

    add_name = st.text_input("선수명 *", placeholder="예: 류현진", key="a_name_input")

    # Team
    st.markdown('<div class="flabel">팀 *</div>', unsafe_allow_html=True)
    atcols = st.columns(len(TEAMS))
    for i, team in enumerate(TEAMS):
        active = st.session_state["a_team"] == team
        with atcols[i]:
            if st.button(team, key=f"a_team__{team}", use_container_width=True, type="primary" if active else "secondary"):
                a_toggle_single("a_team", team); st.rerun()

    # Role
    st.markdown('<div class="flabel">역할 *</div>', unsafe_allow_html=True)
    arcols = st.columns(len(ROLES))
    for i, role in enumerate(ROLES):
        active = st.session_state["a_role"] == role
        with arcols[i]:
            if st.button(role, key=f"a_role__{role}", use_container_width=True, type="primary" if active else "secondary"):
                a_toggle_single("a_role", role); st.rerun()

    card_type_row("카드 종류 *", "a_type", "a")

    add_year = st.text_input("연도 (골글·시그)", placeholder="예: 22, 96, 08", key="a_year_input")

    # Impac
    st.markdown('<div class="flabel">임팩 종류 (임팩 카드)</div>', unsafe_allow_html=True)
    imp_chunks = [IMPAC_TYPES[i:i+8] for i in range(0, len(IMPAC_TYPES), 8)]
    for chunk in imp_chunks:
        aicols = st.columns(8)
        for j, opt in enumerate(chunk):
            active = st.session_state["a_impac"] == opt
            with aicols[j]:
                if st.button(opt, key=f"a_impac__{opt}", use_container_width=True, type="primary" if active else "secondary"):
                    a_toggle_single("a_impac", opt); st.rerun()

    # Pitches
    st.markdown('<div class="flabel">구종 *</div>', unsafe_allow_html=True)
    pitch_chunks = [PITCH_TYPES[i:i+5] for i in range(0, len(PITCH_TYPES), 5)]
    for chunk in pitch_chunks:
        apcols = st.columns(5)
        for j, opt in enumerate(chunk):
            active = opt in st.session_state["a_pitches"]
            with apcols[j]:
                if st.button(opt, key=f"a_pitch__{opt}", use_container_width=True, type="primary" if active else "secondary"):
                    a_toggle_multi("a_pitches", opt); st.rerun()

    st.markdown("---")
    if st.button("✅ 선수 추가", use_container_width=True, type="primary", key="a_submit"):
        err = []
        if not add_name.strip(): err.append("선수명")
        if not st.session_state["a_team"]: err.append("팀")
        if not st.session_state["a_role"]: err.append("역할")
        if not st.session_state["a_type"]: err.append("카드 종류")
        if not st.session_state["a_pitches"]: err.append("구종")
        if err:
            st.error(f"필수 항목을 선택하세요: {', '.join(err)}")
        else:
            ptype = st.session_state["a_type"]
            year_val = None
            yr_s = add_year.strip()
            if yr_s:
                try: year_val = yr_s  # keep as string to preserve leading zeros like "00","01"
                except: pass
            impac_val = st.session_state["a_impac"] if ptype == "임팩" and st.session_state["a_impac"] else None
            st.session_state.players.append({
                "team": st.session_state["a_team"],
                "role": st.session_state["a_role"],
                "raw_prefix": yr_s if ptype in ("골글","시그") else (impac_val or ""),
                "name": add_name.strip(),
                "pitches": list(st.session_state["a_pitches"]),
                "player_type": ptype,
                "year": year_val,
                "impac_type": impac_val,
            })
            save_data(st.session_state.players)
            for k,d in [("a_team",""),("a_role",""),("a_type",""),("a_impac",""),("a_pitches",set())]:
                st.session_state[k] = d
            st.success(f"✅ {add_name.strip()} 추가 완료!")
            st.rerun()

elif "✏️ 선수 편집" in page:
    st.markdown('<div class="section-title">선수 편집 / 삭제</div>', unsafe_allow_html=True)
    players = st.session_state.players

    c1,c2 = st.columns(2)
    with c1: search = st.text_input("선수명 검색")
    with c2: team_f = st.selectbox("팀 필터", ["전체"]+TEAMS)

    filtered = players
    if search: filtered = [p for p in filtered if search in p["name"]]
    if team_f != "전체": filtered = [p for p in filtered if p["team"] == team_f]

    if not filtered:
        st.info("선수를 검색하세요.")
    else:
        opts_labels = [f"{p['name']} ({p['team']}, {p['role']}, {p.get('player_type','')} {p.get('year','') or p.get('impac_type','') or ''})" for p in filtered]
        sel_label = st.selectbox("편집할 선수 선택", opts_labels)
        sel = filtered[opts_labels.index(sel_label)]
        gidx = players.index(sel)

        if st.session_state.get("_etarget") != gidx:
            st.session_state["_etarget"] = gidx
            st.session_state["e_team"] = sel.get("team","")
            st.session_state["e_role"] = sel.get("role","")
            st.session_state["e_type"] = sel.get("player_type","")
            st.session_state["e_impac"] = sel.get("impac_type","") or ""
            st.session_state["e_pitches"] = set(sel.get("pitches",[]))

        def e_single(key, val):
            st.session_state[key] = "" if st.session_state[key] == val else val
        def e_multi(key, val):
            s = st.session_state[key]
            s.discard(val) if val in s else s.add(val)
            st.session_state[key] = s

        st.markdown("---")
        e_name = st.text_input("선수명", value=sel["name"], key=f"e_name_{gidx}")

        # Team
        st.markdown('<div class="flabel">팀</div>', unsafe_allow_html=True)
        etcols = st.columns(len(TEAMS))
        for i, team in enumerate(TEAMS):
            active = st.session_state["e_team"] == team
            with etcols[i]:
                if st.button(team, key=f"e_team__{team}__{gidx}", use_container_width=True, type="primary" if active else "secondary"):
                    e_single("e_team", team); st.rerun()

        # Role
        st.markdown('<div class="flabel">역할</div>', unsafe_allow_html=True)
        ercols = st.columns(len(ROLES))
        for i, role in enumerate(ROLES):
            active = st.session_state["e_role"] == role
            with ercols[i]:
                if st.button(role, key=f"e_role__{role}__{gidx}", use_container_width=True, type="primary" if active else "secondary"):
                    e_single("e_role", role); st.rerun()

        card_type_row("카드 종류", "e_type", f"e{gidx}")

        e_year = st.text_input("연도 (골글·시그)", value=str(sel.get("year") or ""), placeholder="예: 22, 96, 08", key=f"e_year_{gidx}")

        # Impac
        st.markdown('<div class="flabel">임팩 종류 (임팩 카드)</div>', unsafe_allow_html=True)
        imp_chunks = [IMPAC_TYPES[i:i+8] for i in range(0, len(IMPAC_TYPES), 8)]
        for chunk in imp_chunks:
            eicols = st.columns(8)
            for j, opt in enumerate(chunk):
                active = st.session_state["e_impac"] == opt
                with eicols[j]:
                    if st.button(opt, key=f"e_impac__{opt}__{gidx}", use_container_width=True, type="primary" if active else "secondary"):
                        e_single("e_impac", opt); st.rerun()

        # Pitches
        st.markdown('<div class="flabel">구종</div>', unsafe_allow_html=True)
        pitch_chunks = [PITCH_TYPES[i:i+5] for i in range(0, len(PITCH_TYPES), 5)]
        for chunk in pitch_chunks:
            epcols = st.columns(5)
            for j, opt in enumerate(chunk):
                active = opt in st.session_state["e_pitches"]
                with epcols[j]:
                    if st.button(opt, key=f"e_pitch__{opt}__{gidx}", use_container_width=True, type="primary" if active else "secondary"):
                        e_multi("e_pitches", opt); st.rerun()

        st.markdown("---")
        cs, cd = st.columns(2)
        with cs:
            if st.button("💾 저장", use_container_width=True, type="primary", key=f"e_save_{gidx}"):
                ptype = st.session_state["e_type"]
                yr_s = e_year.strip()
                year_val = None
                if yr_s:
                    try: year_val = yr_s  # keep as string to preserve leading zeros
                    except: pass
                impac_val = st.session_state["e_impac"] if ptype == "임팩" and st.session_state["e_impac"] else None
                st.session_state.players[gidx] = {
                    "team": st.session_state["e_team"] or sel["team"],
                    "role": st.session_state["e_role"] or sel["role"],
                    "raw_prefix": yr_s if ptype in ("골글","시그") else (impac_val or ""),
                    "name": e_name,
                    "pitches": list(st.session_state["e_pitches"]),
                    "player_type": ptype or sel.get("player_type",""),
                    "year": year_val,
                    "impac_type": impac_val,
                }
                save_data(st.session_state.players)
                st.session_state["_etarget"] = None
                st.success("✅ 저장 완료!")
                st.rerun()
        with cd:
            if st.button("🗑️ 삭제", use_container_width=True, key=f"e_del_{gidx}"):
                st.session_state.players.pop(gidx)
                save_data(st.session_state.players)
                st.session_state["_etarget"] = None
                st.success("🗑️ 삭제 완료!")
                st.rerun()