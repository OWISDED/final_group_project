import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="MBTI 취향 저격 추천기", page_icon="🎬", layout="wide")

# 임시 데이터베이스 (나중에는 진짜 DB나 API로 바꿔야 해!)
MOCK_DATA = [
    {"title": "인셉션", "type": "영화", "genre": "SF", "platform": "Netflix", "tags": ["#두뇌풀가동", "#SF", "#스릴러"], "mbti": ["INTP", "INTJ", "ENTP"], "img": "https://via.placeholder.com/150/0000FF/808080?Text=Inception", "url": "https://www.netflix.com"},
    {"title": "라라랜드", "type": "영화", "genre": "로맨스", "platform": "Watcha", "tags": ["#로맨스", "#음악", "#감성"], "mbti": ["ENFP", "INFP", "ESFJ"], "img": "https://via.placeholder.com/150/FF0000/FFFFFF?Text=LaLaLand", "url": "https://watcha.com"},
    {"title": "Hype Boy", "type": "음악", "genre": "K-POP", "platform": "Spotify", "tags": ["#신나는", "#KPOP", "#여름"], "mbti": ["ESFP", "ESTP", "ENFJ"], "img": "https://via.placeholder.com/150/00FF00/000000?Text=NewJeans", "url": "https://open.spotify.com"},
    {"title": "잔잔한 클래식", "type": "음악", "genre": "클래식", "platform": "Apple Music", "tags": ["#휴식", "#클래식", "#집중"], "mbti": ["ISTJ", "ISFJ", "INFJ"], "img": "https://via.placeholder.com/150/FFFF00/000000?Text=Classic", "url": "https://music.apple.com"},
]

# 세션 상태 초기화 (리뷰 저장을 위함 - 새로고침해도 날아가지 않게!)
if 'reviews' not in st.session_state:
    st.session_state.reviews = []

st.title("🎬 MBTI & 취향 기반 추천 유니버스 🎧")
st.write("너의 MBTI와 취향을 알려주면 찰떡같은 영화와 음악을 찾아줄게!")

st.divider()

# --- 5번 기능: 일반 검색 및 해시태그 검색 ---
st.subheader("🔍 검색하기")
search_query = st.text_input("제목을 검색하거나, 앞에 #을 붙여서 해시태그를 검색해봐! (예: #로맨스, 인셉션)")

# --- 1 & 2번 기능: MBTI 및 취향 입력 ---
col1, col2, col3 = st.columns(3)

with col1:
    mbti = st.selectbox("1. 당신의 MBTI는 무엇입니까?", 
                        ["모름", "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", 
                         "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"])

with col2:
    genres = st.multiselect("2. 선호하는 장르는?", 
                            ["SF", "로맨스", "스릴러", "코미디", "K-POP", "팝송", "클래식", "힙합"])

with col3:
    platform = st.selectbox("주로 이용하는 플랫폼은?", 
                            ["상관없음", "Netflix", "Watcha", "Spotify", "Apple Music", "YouTube Music"])

st.divider()

# --- 3번 기능: 추천 리스트 로직 및 나열 ---
st.subheader("✨ 당신을 위한 추천 결과")

# 필터링 로직
filtered_data = []
for item in MOCK_DATA:
    match = True
    
    # 검색어 필터링 (#이 있으면 태그 검색, 없으면 제목 검색)
    if search_query:
        if search_query.startswith("#"):
            if search_query not in item["tags"]:
                match = False
        else:
            if search_query.lower() not in item["title"].lower():
                match = False
                
    # 입력 폼 필터링 (검색어가 없을 때만 적용하거나, 함께 적용 가능)
    if not search_query:
        if mbti != "모름" and mbti not in item["mbti"]:
            match = False
        if genres and item["genre"] not in genres:
            match = False
        if platform != "상관없음" and item["platform"] != platform:
            match = False
            
    if match:
        filtered_data.append(item)

# 결과 출력 (이미지 클릭 시 이동 구현)
if filtered_data:
    cols = st.columns(4)
    for i, item in enumerate(filtered_data):
        with cols[i % 4]:
            # HTML을 이용해 클릭 가능한 이미지 생성 (클릭 시 새 창에서 플랫폼 이동)
            clickable_image = f'''
            <a href="{item['url']}" target="_blank">
                <img src="{item['img']}" style="width:100%; border-radius:10px; cursor:pointer;" alt="{item['title']}">
            </a>
            '''
            st.markdown(clickable_image, unsafe_allow_html=True)
            st.markdown(f"**{item['title']}** ({item['platform']})")
            st.caption(" ".join(item["tags"]))
else:
    st.info("조건에 맞는 결과가 없어요. 취향을 조금 바꿔보거나 다른 검색어를 입력해 보세요!")

st.divider()

# 탭 생성
tab1, tab2 = st.tabs(["✨ 추천 유니버스", "💬 리뷰 및 평가"])

with tab1:
    # --- 1, 2, 3번 기능 (검색 및 추천 결과 출력) ---
    st.subheader("🔍 검색하기")
    search_query = st.text_input("제목을 검색하거나, 앞에 #을 붙여서 해시태그를 검색해봐!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        mbti = st.selectbox("1. 당신의 MBTI는?", ["모름", "ISTJ", "ENTP", "INTJ", "ENFP"]) # 리스트 축약함
    with col2:
        genres = st.multiselect("2. 선호하는 장르는?", ["SF", "로맨스", "스릴러", "코미디"])
    with col3:
        platform = st.selectbox("주로 이용하는 플랫폼은?", ["상관없음", "Netflix", "Watcha", "Spotify"])
        
    # (여기에 기존 필터링 및 결과 출력 로직 그대로 삽입)
    
with tab2:
    # --- 4번 기능 (리뷰 폼 및 리스트 출력) ---
    st.subheader("리뷰 남기기")

# 등록된 리뷰 보여주기
if st.session_state.reviews:
    st.write("### 📝 최신 리뷰 모아보기")
    for rev in st.session_state.reviews:
        with st.container():
            st.markdown(f"**{rev['target']}** | {rev['rating']} | 작성자: {rev['name']} `#{rev['mbti']}`")
            st.write(f"> {rev['text']}")
            st.markdown("---")


#수정요소