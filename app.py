import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="MBTI 취향 저격 추천기", page_icon="🎬", layout="wide")

# 임시 데이터베이스 (향후 TMDB API나 CSV 데이터로 교체할 부분)
MOCK_DATA = [
    {
        "title": "인셉션", 
        "genre": "SF", 
        "platform": "Netflix", 
        "tags": ["#두뇌풀가동", "#SF", "#스릴러"], 
        "mbti": ["INTP", "INTJ", "ENTP"], 
        "img": "https://image.tmdb.org/t/p/w500/8Z8dptJE3vewtv4A1BnmTtoZgW3.jpg", 
        "url": "https://www.netflix.com",
        "summary": "타인의 꿈에 들어가 생각을 훔치는 특수 보안요원들의 이야기"
    },
    {
        "title": "라라랜드", 
        "genre": "로맨스", 
        "platform": "Watcha", 
        "tags": ["#로맨스", "#음악", "#감성"], 
        "mbti": ["ENFP", "INFP", "ESFJ"], 
        "img": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0f...jpg", # 예시 이미지 url이 길어 잘릴 경우 대비, 실제 구현시엔 온전한 url 필요
        "url": "https://watcha.com",
        "summary": "재즈 피아니스트와 배우 지망생의 꿈과 사랑을 그린 뮤지컬 영화"
    },
]

# (라라랜드 임시 포스터 복구용 온전한 URL)
MOCK_DATA[1]["img"] = "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Ry0.jpg"

# 세션 상태 초기화 (리뷰 저장용)
if 'reviews' not in st.session_state:
    st.session_state.reviews = []

st.title("🎬 MBTI & 취향 기반 영화 추천기")
st.write("너의 MBTI와 취향을 알려주면 찰떡같은 영화를 찾아줄게!")

st.divider()

# --- 검색 기능 ---
st.subheader("🔍 검색하기")
search_query = st.text_input("제목을 검색하거나, 앞에 #을 붙여서 해시태그를 검색해봐! (예: #로맨스, 인셉션)")

# --- MBTI 및 취향 입력 ---
col1, col2 = st.columns(2)

with col1:
    mbti = st.selectbox("1. 당신의 MBTI는 무엇입니까?", 
                        ["모름", "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", 
                         "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"])

with col2:
    genres = st.multiselect("2. 선호하는 장르는?", 
                            ["SF", "로맨스", "액션", "코미디", "스릴러", "공포", "판타지", "드라마", "범죄/느와르"])

st.divider()

# --- 추천 리스트 로직 ---
st.subheader("✨ 당신을 위한 추천 결과")

filtered_data = []
for item in MOCK_DATA:
    match = True
    
    if search_query:
        if search_query.startswith("#"):
            if search_query not in item["tags"]:
                match = False
        else:
            if search_query.lower() not in item["title"].lower():
                match = False
                
    if not search_query:
        if mbti != "모름" and mbti not in item["mbti"]:
            match = False
        if genres and item["genre"] not in genres:
            match = False
            
    if match:
        filtered_data.append(item)

# --- 결과 출력 및 UI 개선 ---
if filtered_data:
    cols = st.columns(4)
    for i, item in enumerate(filtered_data):
        with cols[i % 4]:
            # 1. 포스터 이미지 오류 수정 (st.image 사용)
            st.image(item["img"], use_container_width=True)
            
            # 2. 제목, 태그, 요약 보여주기
            st.markdown(f"**{item['title']}**")
            st.caption(" ".join(item["tags"]))
            st.write(f"_{item['summary']}_")
            
            # 3. 플랫폼 바로가기 버튼 추가 (st.link_button)
            st.link_button(f"{item['platform']}에서 바로보기 🍿", item['url'], use_container_width=True)
            
            # 4. 리뷰 작성/보기 아코디언 메뉴 (st.expander)
            with st.expander("📝 리뷰 보기 및 작성"):
                # 현재 영화에 해당하는 리뷰만 필터링
                movie_reviews = [r for r in st.session_state.reviews if r['target'] == item['title']]
                if movie_reviews:
                    for rev in movie_reviews:
                        st.markdown(f"**{rev['name']}** `{rev['mbti']}` ({rev['rating']})")
                        st.write(f"> {rev['text']}")
                        st.markdown("---")
                else:
                    st.info("아직 리뷰가 없어요. 첫 리뷰를 남겨보세요!")
                
                # 리뷰 작성 폼
                with st.form(key=f"form_{item['title']}"):
                    new_name = st.text_input("닉네임", key=f"name_{item['title']}")
                    new_rating = st.selectbox("평점", ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"], key=f"rate_{item['title']}")
                    new_text = st.text_area("리뷰 내용", key=f"text_{item['title']}")
                    submit_review = st.form_submit_button("리뷰 등록")
                    
                    if submit_review and new_text:
                        st.session_state.reviews.append({
                            "target": item['title'],
                            "name": new_name if new_name else "익명",
                            "mbti": mbti if mbti != "모름" else "비공개",
                            "rating": new_rating,
                            "text": new_text
                        })
                        st.rerun() # 리뷰 등록 후 화면 새로고침
else:
    st.info("조건에 맞는 결과가 없어요. 취향을 조금 바꿔보거나 다른 검색어를 입력해 보세요!")