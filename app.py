import streamlit as st
import requests
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

# 페이지 기본 설정
st.set_page_config(page_title="MBTI 취향 저격 추천기", page_icon="🎬", layout="wide")

# ---------------------------------------------------------
# 1. 보안 설정: Streamlit 금고에서 TMDB API 키 가져오기
# ---------------------------------------------------------
try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except KeyError:
    st.error("⚠️ 클라우드 Secrets에 TMDB_API_KEY가 없습니다! 설정을 확인해주세요.")
    st.stop()

# ---------------------------------------------------------
# 2. Firebase 초기화 및 DB 연동 (클라우드 배포용)
# ---------------------------------------------------------
if not firebase_admin._apps:
    try:
        raw_json = st.secrets["FIREBASE_JSON"].replace('\n', '').replace('\r', '')
        firebase_secrets = json.loads(raw_json)
        cred = credentials.Certificate(firebase_secrets)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ 파이어베이스 연동 에러가 발생했습니다: {e}")
        st.stop()

# Firestore 데이터베이스 객체 생성
db = firestore.client()

# ---------------------------------------------------------
# 3. 세션 상태 초기화 (현재 접속자 정보 및 화면 상태 기억)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = ""
if 'current_user_mbti' not in st.session_state:
    st.session_state.current_user_mbti = ""
# 더보기 버튼을 위한 영화 표시 개수 상태
if 'movie_limit' not in st.session_state:
    st.session_state.movie_limit = 8
if 'last_mbti' not in st.session_state:
    st.session_state.last_mbti = ""

# ---------------------------------------------------------
# 4. 로그인 & 회원가입 화면
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🎬 MoodFlix")
    st.write("당신의 감성 유형에 맞는 영화를 추천받아보세요.")
    
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with tab1:
        with st.form("login_form"):
            login_id = st.text_input("아이디")
            login_pw = st.text_input("비밀번호", type="password")
            submit_login = st.form_submit_button("입장하기")
            
            if submit_login:
                user_ref = db.collection('users').document(login_id)
                user_doc = user_ref.get()
                
                if user_doc.exists and user_doc.to_dict().get('pw') == login_pw:
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_id
                    st.session_state.current_user_mbti = user_doc.to_dict().get('mbti')
                    st.rerun()
                else:
                    st.error("아이디가 존재하지 않거나 비밀번호가 틀렸습니다!")

    with tab2:
        with st.form("signup_form"):
            new_id = st.text_input("새 아이디")
            new_pw = st.text_input("새 비밀번호", type="password")
            new_mbti = st.selectbox(
    "🌙 당신의 감성 유형을 선택하세요",
    [
        "🌙 감성 몽상가",
        "🌌 별빛 수집가",
        "🌧️ 비 내리는 철학자",
        "🕯️ 추억 여행자",

        "🌸 로맨틱 드리머",
        "🍃 마음 치유사",
        "☕ 카페 속 이야기꾼",
        "🎨 감성 예술가",

        "🧙 세계 탐험가",
        "🚀 우주 개척자",
        "🐉 판타지 수호자",
        "🗺️ 모험 설계자",

        "🔥 도파민 탐험가",
        "⚡ 스릴 헌터",
        "🕶️ 전략가",
        "👑 카리스마 지휘관"
    ]
)
            submit_signup = st.form_submit_button("가입하기")
            
            if submit_signup:
                if len(new_id) < 2 or len(new_pw) < 4:
                    st.warning("아이디는 2자, 비밀번호는 4자 이상 입력해주세요.")
                else:
                    user_ref = db.collection('users').document(new_id)
                    if user_ref.get().exists:
                        st.error("이미 존재하는 아이디입니다.")
                    else:
                        user_ref.set({
                            'pw': new_pw,
                            'mbti': new_mbti
                        })
                        st.success("회원가입 완료! 로그인 탭에서 로그인해주세요.")
                    
    st.stop()

# =========================================================
# 5. 메인 화면 (로그인 성공 시 출력)
# =========================================================
cols = st.columns([8, 2])
with cols[0]:
    st.title("🎬 MoodFlix 감성 큐레이션")
with cols[1]:
    st.write(f"**{st.session_state.current_user}**님 환영합니다!")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

st.divider()

# --- MoodFlix 감성 유형 데이터 ---
MBTI_MAPPING = {

    "🌙 감성 몽상가": {
        "genre": "18",
        "tags": ["#잔잔한", "#여운", "#감성", "#눈물버튼"]
    },

    "🌌 별빛 수집가": {
        "genre": "10749",
        "tags": ["#밤감성", "#사랑", "#설렘", "#몽환적"]
    },

    "🌧️ 비 내리는 철학자": {
        "genre": "9648",
        "tags": ["#생각하게하는", "#철학", "#심리", "#반전"]
    },

    "🕯️ 추억 여행자": {
        "genre": "36",
        "tags": ["#과거", "#추억", "#실화", "#역사"]
    },


    "🌸 로맨틱 드리머": {
        "genre": "10749",
        "tags": ["#첫사랑", "#설렘", "#로맨스", "#행복"]
    },

    "🍃 마음 치유사": {
        "genre": "10751",
        "tags": ["#따뜻한", "#힐링", "#가족", "#위로"]
    },

    "☕ 카페 속 이야기꾼": {
        "genre": "35",
        "tags": ["#일상", "#웃음", "#편안함", "#소소함"]
    },

    "🎨 감성 예술가": {
        "genre": "10402",
        "tags": ["#음악", "#영상미", "#예술", "#분위기"]
    },


    "🧙 세계 탐험가": {
        "genre": "12",
        "tags": ["#모험", "#새로운세계", "#성장", "#여행"]
    },

    "🚀 우주 개척자": {
        "genre": "878",
        "tags": ["#SF", "#미래", "#우주", "#상상력"]
    },

    "🐉 판타지 수호자": {
        "genre": "14",
        "tags": ["#마법", "#전설", "#신비", "#판타지"]
    },

    "🗺️ 모험 설계자": {
        "genre": "28",
        "tags": ["#액션", "#도전", "#스릴", "#짜릿함"]
    },


    "🔥 도파민 탐험가": {
        "genre": "28",
        "tags": ["#속도감", "#폭발", "#전투", "#아드레날린"]
    },

    "⚡ 스릴 헌터": {
        "genre": "53",
        "tags": ["#긴장감", "#공포", "#반전", "#몰입"]
    },

    "🕶️ 전략가": {
        "genre": "80",
        "tags": ["#범죄", "#두뇌싸움", "#치밀함", "#심리전"]
    },

    "👑 카리스마 지휘관": {
        "genre": "10752",
        "tags": ["#전쟁", "#대서사시", "#리더십", "#압도적"]
    }

}

# --- 플랫폼 바로가기 링크 생성 ---
def get_direct_link(platform, title):
    if platform == "Netflix":
        return f"https://www.netflix.com/search?q={title}"
    elif platform == "Watcha":
        return f"https://watcha.com/search?query={title}"
    elif platform == "Disney Plus":
        return f"https://www.disneyplus.com/search?q={title}"
    elif platform == "Wavve":
        return f"https://www.wavve.com/search/search?searchWord={title}"
    else:
        return f"https://www.google.com/search?q={title}+영화+보러가기"

# --- TMDB API 영화 데이터 요청 함수 ---
@st.cache_data(show_spinner=False)
def fetch_movies_by_mbti(mbti_type):
    genre_id = MBTI_MAPPING[mbti_type]["genre"]
    tags = MBTI_MAPPING[mbti_type]["tags"]
    
    movie_data_list = []
    
    # 총 24개(기본 8개 + 더보기 16개)의 영화를 가져오기 위해 1~2페이지를 순회
    for page in range(1, 3):
        # [수정됨] 마이너한 영화 제외 필터 추가 (한국어/영어, 투표수 500개 이상)
        discover_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&language=ko-KR&sort_by=popularity.desc&with_genres={genre_id}&with_original_language=ko|en&vote_count.gte=500&page={page}"
        movies_res = requests.get(discover_url).json()
        
        for movie in movies_res.get('results', []):
            if len(movie_data_list) >= 24: # 24개까지만 수집
                break
                
            movie_id = movie['id']
            provider_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
            provider_res = requests.get(provider_url).json()
            
            platform = "Google 검색"
            if 'KR' in provider_res.get('results', {}) and 'flatrate' in provider_res['results']['KR']:
                platform = provider_res['results']['KR']['flatrate'][0]['provider_name']
                
            direct_url = get_direct_link(platform, movie['title'])
                
            movie_data_list.append({
                "title": movie['title'],
                "platform": platform,
                "tags": tags + [f"#{platform.replace(' ', '')}"],
                "img": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie['poster_path'] else "https://via.placeholder.com/500x750?text=No+Image",
                "url": direct_url,
                "summary": movie['overview'][:80] + "..." if movie['overview'] else "요약 정보가 없습니다."
            })
            
        if len(movie_data_list) >= 24:
            break
            
    return movie_data_list

# ---------------------------------------------------------
# 6. 영화 추천 및 리뷰 UI 
# ---------------------------------------------------------
st.subheader("🔍 내 감성 유형에 맞는 추천작 보기")
current_mbti_idx = list(MBTI_MAPPING.keys()).index(st.session_state.current_user_mbti)
selected_mbti = st.selectbox("어떤 감성 유형을 볼까요?", list(MBTI_MAPPING.keys()), index=current_mbti_idx)

# MBTI를 새로 선택하면 화면에 보여줄 영화 개수를 다시 8개로 초기화
if st.session_state.last_mbti != selected_mbti:
    st.session_state.movie_limit = 8
    st.session_state.last_mbti = selected_mbti

with st.spinner('해외 서버에서 영화 데이터를 가져오는 중입니다... 🍿'):
    # 캐싱된 함수 호출 (최대 24개의 데이터 로드)
    ALL_RECOMMENDED_MOVIES = fetch_movies_by_mbti(selected_mbti)

st.subheader(f"✨ {selected_mbti} 맞춤 추천 결과")

if ALL_RECOMMENDED_MOVIES:
    # 세션에 저장된 limit 만큼만 슬라이싱하여 보여줌
    movies_to_display = ALL_RECOMMENDED_MOVIES[:st.session_state.movie_limit]
    
    cols = st.columns(4)
    for i, item in enumerate(movies_to_display):
        with cols[i % 4]:
            st.image(item["img"], use_container_width=True)
            st.markdown(f"**{item['title']}**")
            st.caption(" ".join(item["tags"]))
            st.write(f"_{item['summary']}_")
            st.link_button(f"{item['platform']}에서 바로보기 🍿", item['url'], use_container_width=True)
            
            # --- 리뷰 기능 ---
            with st.expander("📝 리뷰 보기 및 작성"):
                reviews_ref = db.collection('reviews').where('target', '==', item['title']).stream()
                movie_reviews = [{"id": r.id, **r.to_dict()} for r in reviews_ref]
                
                if movie_reviews:
                    for rev in movie_reviews:
                        st.markdown(f"**{rev['name']}** `{rev['mbti']}` ({rev['rating']})")
                        st.write(f"> {rev['text']}")
                        
                        if rev['name'] == st.session_state.current_user:
                            if st.button("🗑️ 삭제", key=f"del_{rev['id']}_{i}"):
                                db.collection('reviews').document(rev['id']).delete()
                                st.rerun() 
                        st.markdown("---")
                else:
                    st.info("아직 리뷰가 없어요. 첫 리뷰를 남겨보세요!")
                
                with st.form(key=f"form_{item['title']}_{i}"):
                    st.write(f"작성자: **{st.session_state.current_user}**")
                    new_rating = st.selectbox("평점", ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"], key=f"rate_{item['title']}_{i}")
                    new_text = st.text_area("리뷰 내용", key=f"text_{item['title']}_{i}")
                    submit_review = st.form_submit_button("리뷰 등록")
                    
                    if submit_review and new_text:
                        new_review_id = str(time.time()) 
                        db.collection('reviews').document(new_review_id).set({
                            "target": item['title'],
                            "name": st.session_state.current_user,
                            "mbti": st.session_state.current_user_mbti,
                            "rating": new_rating,
                            "text": new_text
                        })
                        st.rerun() 
                        
    # --- [수정됨] 더 보기 버튼 UI ---
    st.write("") # 여백 추가
    
    # 24개 미만으로 보여지고 있을 때만 '더 보기' 버튼 노출
    if st.session_state.movie_limit < len(ALL_RECOMMENDED_MOVIES):
        # 중앙 정렬을 위해 컬럼 활용
        _, center_col, _ = st.columns([4, 2, 4])
        with center_col:
            if st.button("🔽 추천 영화 더 보기 (16개 추가)", use_container_width=True):
                # 표시할 영화 개수를 24개로 고정 (8 + 16 = 24)
                st.session_state.movie_limit = 24
                st.rerun()
else:
    st.info("추천할 영화를 찾지 못했습니다.")
