import streamlit as st
import requests
import time # [추가된 부분] 리뷰 삭제용 고유 ID 생성을 위해 필요

st.set_page_config(page_title="김지환의 MBTI 취향 저격 추천기", page_icon="🎬", layout="wide")

TMDB_API_KEY = "70a1f69ea753311b6a7a71f9e02599c4"

# ---------------------------------------------------------
# [추가된 부분] 1. 세션 상태 초기화 (로그인 정보, 리뷰 데이터)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = ""
if 'reviews' not in st.session_state:
    st.session_state.reviews = [] # 리뷰 저장소

# ---------------------------------------------------------
# [추가된 부분] 2. 간단한 로그인 화면 구현
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🎬 영화 추천 서비스 로그인")
    st.write("서비스를 이용하려면 닉네임을 입력해주세요!")
    
    with st.form("login_form"):
        username = st.text_input("닉네임 (아이디)")
        submit_login = st.form_submit_button("입장하기")
        
        if submit_login:
            if username.strip() == "":
                st.error("닉네임을 입력해주세요!")
            else:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.rerun() # 화면 새로고침하여 메인 페이지로 이동
                
    st.stop() # 로그인이 안 되어있으면 아래 코드(메인 화면)를 실행하지 않고 멈춤

# =========================================================
# 여기서부터는 로그인 성공 시 보여지는 메인 화면입니다.
# =========================================================

# [추가된 부분] 상단 네비게이션 바 (로그아웃 기능)
cols = st.columns([8, 2])
with cols[0]:
    st.title("🎬 MBTI & 취향 기반 추천")
with cols[1]:
    st.write(f"환영합니다, **{st.session_state.current_user}**님!")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

st.write("너의 MBTI와 취향을 알려주면 찰떡같은 영화를 찾아줄게!")
st.divider()

# --- (이하 TMDB API 데이터 가져오기 로직은 동일합니다) ---
@st.cache_data
def fetch_movie_data(title):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=ko-KR&query={title}"
    search_res = requests.get(search_url).json()
    
    if not search_res.get('results'):
        return None
        
    movie = search_res['results'][0]
    movie_id = movie['id']
    
    provider_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
    provider_res = requests.get(provider_url).json()
    
    platform = "정보 없음"
    url = f"https://www.google.com/search?q={title}+영화"
    
    if 'KR' in provider_res.get('results', {}) and 'flatrate' in provider_res['results']['KR']:
        platform = provider_res['results']['KR']['flatrate'][0]['provider_name']
        url = provider_res['results']['KR']['link']
        
    return {
        "title": movie['title'],
        "genre": "영화",
        "platform": platform,
        "tags": [f"#{platform.replace(' ', '')}", "#추천영화"],
        "mbti": ["INTP", "ENFP", "ISFJ"],
        "img": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}",
        "url": url,
        "summary": movie['overview'][:80] + "..." if movie['overview'] else "요약 정보가 없습니다."
    }

movie_list = ["인셉션", "라라랜드", "어벤져스", "기생충", "인터스텔라"]

MOCK_DATA = []
for title in movie_list:
    data = fetch_movie_data(title)
    if data:
        MOCK_DATA.append(data)


# ---------------------------------------------------------
# [수정된 부분] 3. 누락되었던 필터링 UI 및 로직 복구
# ---------------------------------------------------------
st.subheader("🔍 검색 및 취향 입력")
search_query = st.text_input("제목이나 해시태그(#)를 검색해봐!")

col1, col2 = st.columns(2)
with col1:
    mbti = st.selectbox("1. 당신의 MBTI는 무엇입니까?", 
                        ["모름", "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", 
                         "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"])
with col2:
    genres = st.multiselect("2. 선호하는 장르는?", 
                            ["SF", "로맨스", "액션", "코미디", "스릴러", "공포", "판타지", "드라마", "범죄/느와르"])

st.divider()

# 데이터 필터링 과정
filtered_data = []
for item in MOCK_DATA:
    match = True
    if search_query:
        if search_query.startswith("#") and search_query not in item["tags"]:
            match = False
        elif not search_query.startswith("#") and search_query.lower() not in item["title"].lower():
            match = False
            
    if not search_query:
        if mbti != "모름" and mbti not in item["mbti"]:
            match = False
        # (API에서 장르를 '영화'로 통일해두었기 때문에, 현재 장르 필터는 구동 테스트용으로만 존재합니다)
        if genres and item["genre"] not in genres:
            match = False
            
    if match:
        filtered_data.append(item)


# ---------------------------------------------------------
# [수정된 부분] 4. 결과 출력 및 리뷰 삭제 기능 추가
# ---------------------------------------------------------
st.subheader("✨ 당신을 위한 추천 결과")

if filtered_data:
    cols = st.columns(4)
    for i, item in enumerate(filtered_data):
        with cols[i % 4]:
            st.image(item["img"], use_container_width=True)
            st.markdown(f"**{item['title']}**")
            st.caption(" ".join(item["tags"]))
            st.write(f"_{item['summary']}_")
            st.link_button(f"{item['platform']}에서 바로보기 🍿", item['url'], use_container_width=True)
            
            # 리뷰 아코디언 메뉴
            with st.expander("📝 리뷰 보기 및 작성"):
                # 현재 영화의 리뷰만 불러오기
                movie_reviews = [r for r in st.session_state.reviews if r['target'] == item['title']]
                
                if movie_reviews:
                    for rev in movie_reviews:
                        st.markdown(f"**{rev['name']}** `{rev['mbti']}` ({rev['rating']})")
                        st.write(f"> {rev['text']}")
                        
                        # [추가된 부분] 현재 접속자와 리뷰 작성자가 같으면 '삭제' 버튼 노출
                        if rev['name'] == st.session_state.current_user:
                            if st.button("🗑️ 리뷰 삭제", key=f"del_{rev['id']}"):
                                # 해당 고유 ID를 가진 리뷰만 리스트에서 제거
                                st.session_state.reviews = [r for r in st.session_state.reviews if r['id'] != rev['id']]
                                st.rerun() # 삭제 후 즉시 화면 새로고침
                                
                        st.markdown("---")
                else:
                    st.info("아직 리뷰가 없어요. 첫 리뷰를 남겨보세요!")
                
                # 리뷰 작성 폼
                with st.form(key=f"form_{item['title']}"):
                    # [수정된 부분] 작성자 이름은 로그인한 사용자로 고정 (입력창 제거)
                    st.write(f"작성자: **{st.session_state.current_user}**")
                    new_rating = st.selectbox("평점", ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"], key=f"rate_{item['title']}")
                    new_text = st.text_area("리뷰 내용", key=f"text_{item['title']}")
                    submit_review = st.form_submit_button("리뷰 등록")
                    
                    if submit_review and new_text:
                        st.session_state.reviews.append({
                            "id": str(time.time()), # [추가된 부분] 삭제를 식별하기 위한 고유 ID (현재 시간 활용)
                            "target": item['title'],
                            "name": st.session_state.current_user, # 로그인한 사용자 이름 저장
                            "mbti": mbti if mbti != "모름" else "비공개",
                            "rating": new_rating,
                            "text": new_text
                        })
                        st.rerun() 
else:
    st.info("조건에 맞는 결과가 없어요. 취향을 조금 바꿔보거나 다른 검색어를 입력해 보세요!")