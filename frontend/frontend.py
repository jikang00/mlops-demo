import os
import streamlit as st
import requests

API_URL = os.getenv(
    "API_URL",
    "http://localhost:8000/summarize"
)

HISTORY_URL = API_URL.replace(
    "/summarize",
    "/history"
)

st.set_page_config(
    page_title="Hugging Face Summarizer"
)

# 사이드바 메뉴 설정
page = st.sidebar.radio(
    "메뉴",
    ["요약하기", "히스토리"]
)

# =========================
# 1. 요약하기 페이지
# =========================
if page == "요약하기":

    st.title("Hugging Face 모델 기반 텍스트 요약")

    url = st.text_input(
        "기사 URL",
        placeholder="https://..."
    )

    model = st.selectbox(
        "모델 선택",
        [
            "facebook/bart-large-cnn",
            "google-t5/t5-small",
            "/models/t5-small"
        ]
    )

    max_length = st.slider(
        "최대 길이",
        50,
        300,
        150
    )

    min_length = st.slider(
        "최소 길이",
        20,
        100,
        40
    )

    if st.button("요약하기"):

        if not url:
            st.warning("URL을 입력하세요.")

        else:

            with st.spinner("요약 중입니다..."):

                try:

                    response = requests.post(
                        API_URL,
                        json={
                            "url": url,
                            "model": model,
                            "max_length": max_length,
                            "min_length": min_length
                        }
                    )

                    if response.status_code == 200:

                        result = response.json()

                        st.success("요약 완료")

                        st.markdown("### 선택한 모델")
                        st.write(result["model"])

                        st.markdown("### 요약 결과")
                        st.write(result["summary"])

                    else:
                        st.error(response.text)

                except requests.exceptions.RequestException as e:

                    st.error(
                        f"Backend 연결 오류: {e}"
                    )


# =========================
# 2. 히스토리 페이지
# =========================
elif page == "히스토리":

    st.title("요약 히스토리")

    try:

        response = requests.get(HISTORY_URL)

        if response.status_code != 200:

            st.error(
                f"히스토리 조회 실패: {response.text}"
            )

        else:

            histories = response.json()

            if not histories:

                st.info("저장된 요약 기록이 없습니다.")

            else:

                for item in histories:

                    with st.expander(
                        f"{item['created_at']} | {item['model']}"
                    ):

                        st.markdown("### 기사 URL")
                        st.write(item["url"])

                        st.markdown("### 모델")
                        st.write(item["model"])

                        st.markdown("### 요약 결과")
                        st.write(item["summary"])

                        st.markdown(
                            f"최대 길이: {item['max_length']} / "
                            f"최소 길이: {item['min_length']}"
                        )

    except requests.exceptions.RequestException as e:

        st.error(
            f"Backend 연결 오류: {e}"
        )
