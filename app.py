import streamlit as st
import requests
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# 페이지 기본 설정
st.set_page_config(page_title="김지환의 MBTI 취향 저격 추천기", page_icon="🎬", layout="wide")

# ---------------------------------------------------------
# 1. 보안 설정: Streamlit 금고에서 TMDB API 키 가져오기
# ---------------------------------------------------------
try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except KeyError:
    st.error("⚠️ .streamlit/secrets.toml 파일에 TMDB_API_KEY가 없습니다! 설정을 확인해주세요.")
    st.stop()

# ---------------------------------------------------------
# 2. Firebase 초기화 및 DB 연동
# ---------------------------------------------------------
# Streamlit 특성상 반복 실행 시 중복 초기화를 방지합니다.
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate('firebase_key.json') 
        firebase_admin.initialize_app(cred)
    except FileNotFoundError:
        st.error("⚠️ firebase_key.json 파일을 찾을 수 없습니다! 파일명과 위치를 확인해주세요.")
        st.stop()

# Firestore 데이터베이스 객체 생성
db = firestore.client()

# ---------------------------------------------------------
# 3. 세션 상태 초기화 (현재 접속자 정보 기억)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = ""
if 'current_user_mbti' not in st.session_state:
    st.session_state.current_user_mbti = ""

# ---------------------------------------------------------
# 4. 로그인 & 회원가입 화면
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🎬 영화 추천 서비스")
    st.write("나의 MBTI에 딱 맞는 영화를 추천받아보세요!")
    
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
            new_mbti = st.selectbox("당신의 MBTI는?", 
                        ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", 
                         "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"])
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
                    
    st.stop() # 로그인 안 되었을 땐 여기서 화면 렌더링 멈춤

# =========================================================
# 5. 메인 화면 (로그인 성공 시 출력)
# =========================================================
cols = st.columns([8, 2])
with cols[0]:
    st.title("🎬 MBTI & 취향 기반 추천")
with cols[1]:
    st.write(f"**{st.session_state.current_user}**님 (`{st.session_state.current_user_mbti}`) 환영합니다!")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

st.divider()

# --- MBTI 장르 매핑 데이터 ---
MBTI_MAPPING = {
    "INTP": {"genre": "878", "tags": ["#두뇌풀가동", "#SF", "#논리적"]},
    "INFP": {"genre": "14", "tags": ["#상상력자극", "#판타지", "#몽환적"]},
    "ENTP": {"genre": "35", "tags": ["#도파민폭발", "#코미디", "#유쾌함"]},
    "ENFP": {"genre": "10749", "tags": ["#몽글몽글", "#로맨스", "#감수성"]},
    "INTJ": {"genre": "9648", "tags": ["#치밀한전개", "#미스터리", "#스릴러"]},
    "INFJ": {"genre": "18", "tags": ["#여운이가득", "#드라마", "#인생영화"]},
    "ENTJ": {"genre": "80", "tags": ["#카리스마", "#범죄/느와르", "#긴장감"]},
    "ENFJ": {"genre": "10751", "tags": ["#따뜻한", "#가족", "#감동적인"]},
    "ISTP": {"genre": "28", "tags": ["#타격감", "#액션", "#시원한"]},
    "ISFP": {"genre": "16", "tags": ["#아름다운", "#애니메이션", "#힐링"]},
    "ESTP": {"genre": "12", "tags": ["#아드레날린", "#어드벤처", "#모험"]},
    "ESFP": {"genre": "10402", "tags": ["#흥겨운", "#음악", "#신나는"]},
    "ISTJ": {"genre": "36", "tags": ["#고증철저", "#역사", "#실화바탕"]},
    "ISFJ": {"genre": "10770", "tags": ["#잔잔한", "#TV영화", "#편안한"]},
    "ESTJ": {"genre": "10752", "tags": ["#스케일큰", "#전쟁", "#압도적"]},
    "ESFJ": {"genre": "35", "tags": ["#다같이보기좋은", "#코미디", "#웃음"]}
}

# --- 플랫폼 바로가기 링크 생성기 ---
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
    discover_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&language=ko-KR&sort_by=popularity.desc&with_genres={genre_id}&page=1"
    movies_res = requests.get(discover_url).json()
    
    movie_data_list = []
    # 상위 8개 영화만 출력
    for movie in movies_res.get('results', [])[:8]:
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
    return movie_data_list

# ---------------------------------------------------------
# 6. 영화 추천 및 리뷰 UI 영역
# ---------------------------------------------------------
st.subheader("🔍 내 MBTI에 맞는 추천작 보기")
# 기본 선택값을 로그인한 유저의 MBTI로 설정
current_mbti_idx = list(MBTI_MAPPING.keys()).index(st.session_state.current_user_mbti)
selected_mbti = st.selectbox("어떤 MBTI의 추천 영화를 볼까요?", list(MBTI_MAPPING.keys()), index=current_mbti_idx)

with st.spinner('해외 서버에서 영화 데이터를 가져오는 중입니다... 🍿'):
    RECOMMENDED_MOVIES = fetch_movies_by_mbti(selected_mbti)

st.subheader(f"✨ {selected_mbti} 맞춤 추천 결과")

if RECOMMENDED_MOVIES:
    cols = st.columns(4)
    for i, item in enumerate(RECOMMENDED_MOVIES):
        with cols[i % 4]:
            st.image(item["img"], use_container_width=True)
            st.markdown(f"**{item['title']}**")
            st.caption(" ".join(item["tags"]))
            st.write(f"_{item['summary']}_")
            st.link_button(f"{item['platform']}에서 바로보기 🍿", item['url'], use_container_width=True)
            
            # --- 리뷰 기능 (Firebase 연동) ---
            with st.expander("📝 리뷰 보기 및 작성"):
                # Firebase에서 이 영화에 달린 리뷰만 가져오기
                reviews_ref = db.collection('reviews').where('target', '==', item['title']).stream()
                movie_reviews = [{"id": r.id, **r.to_dict()} for r in reviews_ref]
                
                # 리뷰 목록 출력
                if movie_reviews:
                    for rev in movie_reviews:
                        st.markdown(f"**{rev['name']}** `{rev['mbti']}` ({rev['rating']})")
                        st.write(f"> {rev['text']}")
                        
                        # 내가 쓴 리뷰면 삭제 버튼 노출
                        if rev['name'] == st.session_state.current_user:
                            if st.button("🗑️ 삭제", key=f"del_{rev['id']}"):
                                db.collection('reviews').document(rev['id']).delete() # Firebase에서 영구 삭제
                                st.rerun() 
                        st.markdown("---")
                else:
                    st.info("아직 리뷰가 없어요. 첫 리뷰를 남겨보세요!")
                
                # 리뷰 작성 폼
                with st.form(key=f"form_{item['title']}"):
                    st.write(f"작성자: **{st.session_state.current_user}**")
                    new_rating = st.selectbox("평점", ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"], key=f"rate_{item['title']}")
                    new_text = st.text_area("리뷰 내용", key=f"text_{item['title']}")
                    submit_review = st.form_submit_button("리뷰 등록")
                    
                    if submit_review and new_text:
                        new_review_id = str(time.time()) 
                        db.collection('reviews').document(new_review_id).set({
                            "target": item['title'],
                            "name": st.session_state.current_user,
                            "mbti": st.session_state.current_user_mbti,
                            "rating": new_rating,
                            "text": new_text
                        }) # Firebase에 새 리뷰 영구 저장
                        st.rerun() 
else:
    st.info("추천할 영화를 찾지 못했습니다.")