import streamlit as st
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import time

# ==========================================
# 페이지 설정
# ==========================================

st.set_page_config(
    page_title="MoodFlix",
    page_icon="💜",
    layout="centered"
)

# ==========================================
# 디자인
# ==========================================

st.markdown("""
<style>

/* 전체 배경 */
.stApp {
    background-color: #FAFAFF;
}

/* 제목 */
h1,h2,h3 {
    text-align:center;
}

/* 버튼 */
div.stButton > button:first-child {
    background-color:#E6E6FA;
    color:black;
    border-radius:15px;
    border:2px solid #DCD0FF;
    font-weight:bold;
    transition:0.3s;
}

div.stButton > button:first-child:hover {
    background-color:#B026FF;
    color:white;
}

/* 입력창 */
.stTextInput input,
.stTextArea textarea {
    background-color:white !important;
    color:black !important;
    border-radius:10px;
}

/* 카드 */
.movie-card {
    background:white;
    padding:15px;
    border-radius:18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    margin-bottom:15px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# API KEY
# ==========================================

try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except:
    st.error("TMDB_API_KEY가 없습니다.")
    st.stop()

# ==========================================
# Firebase
# ==========================================

if not firebase_admin._apps:
    try:
        firebase_json = json.loads(
            st.secrets["FIREBASE_JSON"]
        )

        cred = credentials.Certificate(firebase_json)

        firebase_admin.initialize_app(cred)

    except Exception as e:
        st.error(f"Firebase 오류: {e}")
        st.stop()

db = firestore.client()

# ==========================================
# 세션 상태
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "step" not in st.session_state:
    st.session_state.step = 0

if "answers" not in st.session_state:
    st.session_state.answers = []

if "movie_limit" not in st.session_state:
    st.session_state.movie_limit = 4

if "celebrated" not in st.session_state:
    st.session_state.celebrated = False

# ==========================================
# MBTI 데이터
# ==========================================

MOOD_PROFILES = {
@st.cache_data(show_spinner=False)
def fetch_movies(genre_id):

    discover_url = (
        f"https://api.themoviedb.org/3/discover/movie"
        f"?api_key={TMDB_API_KEY}"
        f"&language=ko-KR"
        f"&sort_by=popularity.desc"
        f"&with_genres={genre_id}"
        f"&vote_count.gte=500"
        f"&page=1"
    )

    res = requests.get(
        discover_url
    ).json()

    return res.get(
        "results",
        []
    )[:20]
    st.subheader(
        "🍿 당신을 위한 추천 영화"
    )

    with st.spinner(
        "💜 감성 분석 중..."
    ):

        movies = fetch_movies(
            profile["genre"]
        )

    for movie in movies[
        :st.session_state.movie_limit
    ]:

        st.markdown(
            '<div class="movie-card">',
            unsafe_allow_html=True
        )
        with st.expander("📝 리뷰 보기 및 작성"):

            reviews_ref = (
                db.collection("reviews")
                .where("target", "==", movie["title"])
                .stream()
            )

            movie_reviews = [
                {
                    "id": r.id,
                    **r.to_dict()
                }
                for r in reviews_ref
            ]

            if movie_reviews:

                for rev in movie_reviews:

                    st.markdown(
                        f"**{rev['name']}**"
                    )

                    st.write(
                        f"> {rev['text']}"
                    )

                    if (
                        rev["name"]
                        ==
                        st.session_state.current_user
                    ):

                        if st.button(
                            "🗑️ 삭제",
                            key=f"del_{rev['id']}"
                        ):

                            db.collection(
                                "reviews"
                            ).document(
                                rev["id"]
                            ).delete()

                            st.rerun()

                    st.markdown("---")

            else:

                st.info(
                    "첫 리뷰를 남겨보세요!"
                )
        with st.expander("📝 리뷰 보기 및 작성"):

            reviews_ref = (
                db.collection("reviews")
                .where("target", "==", movie["title"])
                .stream()
            )

            movie_reviews = [
                {
                    "id": r.id,
                    **r.to_dict()
                }
                for r in reviews_ref
            ]

            if movie_reviews:

                for rev in movie_reviews:

                    st.markdown(
                        f"**{rev['name']}**"
                    )

                    st.write(
                        f"> {rev['text']}"
                    )

                    if (
                        rev["name"]
                        ==
                        st.session_state.current_user
                    ):

                        if st.button(
                            "🗑️ 삭제",
                            key=f"del_{rev['id']}"
                        ):

                            db.collection(
                                "reviews"
                            ).document(
                                rev["id"]
                            ).delete()

                            st.rerun()

                    st.markdown("---")

            else:

                st.info(
                    "첫 리뷰를 남겨보세요!"
                )
        if movie.get("poster_path"):

            st.image(
                f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            )

        st.markdown(
            f"### {movie['title']}"
        )

        st.write(
            movie.get(
                "overview",
                "줄거리 없음"
            )[:120]
            + "..."
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )
    if (
        st.session_state.movie_limit
        < len(movies)
    ):

        if st.button(
            "🔽 영화 더 보기"
        ):

            st.session_state.movie_limit += 4

            st.rerun()
    "INFP":{"title":"새벽 세 시, 빗소리를 닮은 몽상가","genre":"18"},
    "INFJ":{"title":"깊은 밤, 숨겨진 의미를 찾는 철학자","genre":"9648"},
    "ENFP":{"title":"네온사인 아래 춤추는 페스티벌 러버","genre":"10749"},
    "ENFJ":{"title":"다 함께 울고 웃는 심야 극장의 영웅","genre":"10751"},
    "INTP":{"title":"조용한 다락방의 분석가","genre":"878"},
    "INTJ":{"title":"안개 낀 심야 영화관의 설계자","genre":"53"},
    "ENTP":{"title":"반전 무비 디렉터","genre":"80"},
    "ENTJ":{"title":"마스터 프로듀서","genre":"28"},
    "ISFP":{"title":"헤드폰 속 우주의 아티스트","genre":"10402"},
    "ISFJ":{"title":"기억 보관자","genre":"36"},
    "ESFP":{"title":"스포트라이트 팝스타","genre":"10402"},
    "ESFJ":{"title":"취향 공유 호스트","genre":"35"},
    "ISTP":{"title":"시네마 스나이퍼","genre":"28"},
    "ISTJ":{"title":"클래식 수집가","genre":"36"},
    "ESTP":{"title":"스릴 러버","genre":"28"},
    "ESTJ":{"title":"명작 큐레이터","genre":"18"}
}


# ==========================================
# 로그인 / 회원가입
# ==========================================

if not st.session_state.logged_in:

    st.markdown("""
    <h1 style='text-align:center;color:#7B2FF7;'>
    💜 MoodFlix
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p style='text-align:center;font-size:18px;'>
    당신의 미디어 감성 DNA를 찾아보세요
    </p>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])

    # -------------------
    # 로그인
    # -------------------

    with tab1:

        with st.form("login_form"):

            login_id = st.text_input("아이디")

            login_pw = st.text_input(
                "비밀번호",
                type="password"
            )

            login_submit = st.form_submit_button("입장하기")

            if login_submit:

                user_ref = db.collection("users").document(login_id)

                user_doc = user_ref.get()

                if (
                    user_doc.exists
                    and user_doc.to_dict()["pw"] == login_pw
                ):

                    st.session_state.logged_in = True

                    st.session_state.current_user = login_id

                    st.rerun()

                else:

                    st.error(
                        "아이디 또는 비밀번호가 틀렸습니다."
                    )

    # -------------------
    # 회원가입
    # -------------------

    with tab2:

        with st.form("signup_form"):

            new_id = st.text_input("새 아이디")

            new_pw = st.text_input(
                "새 비밀번호",
                type="password"
            )

            signup_submit = st.form_submit_button(
                "회원가입"
            )

            if signup_submit:

                if len(new_id) < 2:

                    st.warning(
                        "아이디는 2자 이상 입력해주세요."
                    )

                elif len(new_pw) < 4:

                    st.warning(
                        "비밀번호는 4자 이상 입력해주세요."
                    )

                else:

                    user_ref = db.collection(
                        "users"
                    ).document(new_id)

                    if user_ref.get().exists:

                        st.error(
                            "이미 존재하는 아이디입니다."
                        )

                    else:

                        user_ref.set({
                            "pw": new_pw
                        })

                        st.success(
                            "회원가입 완료!"
                        )

    st.stop()


# ==========================================
# 테스트 공통 함수
# ==========================================

def next_step(answer):
    st.session_state.answers.append(answer)
    st.session_state.step += 1
    st.rerun()

# ==========================================
# 로그인 후 메인
# ==========================================

cols = st.columns([8,2])

with cols[0]:
    st.markdown("""
    <h1 style='text-align:left;color:#7B2FF7;'>
    💜 MoodFlix
    </h1>
    """, unsafe_allow_html=True)

with cols[1]:

   if st.button("로그아웃"):

    st.session_state.logged_in = False

    st.session_state.current_user = ""

    st.session_state.step = 0

    st.session_state.answers = []

    st.session_state.movie_limit = 4

    st.session_state.celebrated = False

    st.rerun()

st.divider()


if st.session_state.step == 0:

    st.progress(25)

    st.subheader(
        "🎧 금요일 밤, 당신의 선택은?"
    )

    if st.button(
        "✨ 친구들과 신나게 놀러간다"
    ):
        next_step("E")

    if st.button(
        "🕯️ 집에서 혼자 쉰다"
    ):
        next_step("I")
elif st.session_state.step == 1:

    st.progress(50)

    st.subheader(
        "🎬 어떤 영화가 끌리나요?"
    )

    if st.button(
        "🔍 현실적인 이야기"
    ):
        next_step("S")

    if st.button(
        "🌌 상상력 넘치는 세계관"
    ):
        next_step("N")
elif st.session_state.step == 2:

    st.progress(75)

    st.subheader(
        "🎵 친구에게 노래를 추천한다면?"
    )

    if st.button(
        "🤯 비트와 편곡이 미쳤다"
    ):
        next_step("T")

    if st.button(
        "🥺 감정선이 너무 좋다"
    ):
        next_step("F")
elif st.session_state.step == 3:

    st.progress(100)

    st.subheader(
        "🚗 드라이브 플레이리스트는?"
    )

    if st.button(
        "🗂️ 미리 계획해서 준비"
    ):
        next_step("J")

    if st.button(
        "🎲 랜덤 셔플"
    ):
        next_step("P")
elif st.session_state.step == 4:

    if not st.session_state.celebrated:

        st.balloons()

        st.session_state.celebrated = True

    mbti_result = "".join(
        st.session_state.answers
    )

    profile = MOOD_PROFILES.get(
        mbti_result,
        MOOD_PROFILES["INFP"]
    )

    st.markdown("---")

    st.markdown(
        f"""
        <h3>
        당신의 미디어 감성 DNA는...
        </h3>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <h1 style='color:#7B2FF7;'>
        💜 {profile['title']}
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        f"({mbti_result})"
    )

    st.markdown("---")
    st.write("")

    if st.button(
        "🔄 테스트 다시하기"
    ):

        st.session_state.step = 0

        st.session_state.answers = []

        st.session_state.movie_limit = 4

        st.session_state.celebrated = False

        st.rerun()
