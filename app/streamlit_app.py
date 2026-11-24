"""App demo: gợi ý phim, chấm điểm (ghi vào DB app -> CDC), tìm phim bằng câu mô tả, theo dõi pipeline.

Chạy: streamlit run app/streamlit_app.py
"""
from datetime import date, datetime, timezone
import json
import os
import sys
import threading
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai import embeddings  # noqa: E402
from ai.hybrid import HybridRecommender  # noqa: E402
from app import journey  # noqa: E402
from transform.gold import OCCUPATION as OCCUPATIONS  # noqa: E402
from pipeline import config  # noqa: E402

st.set_page_config(page_title="Movie Platform", page_icon="🎬", layout="wide")
AIRFLOW = os.getenv("AIRFLOW_URL", "http://localhost:8081")
DEMO_ALPHA = 0.7   # α mặc định khi so sánh gợi ý trước / sau


@st.cache_resource
def warm_up_encoder():
    """Tải mô hình E5 (~40 giây) ở luồng nền ngay khi mở app, để lần tìm kiếm đầu không phải chờ."""
    t = threading.Thread(target=embeddings.model, daemon=True)
    t.start()
    return t


warm_up_encoder()


def show_poster(url, width=None):
    """Ảnh đại diện bài Wikipedia; phim chưa có ảnh thì hiện khung xám."""
    if isinstance(url, str) and url:
        if width:
            st.image(url, width=width)
        else:
            st.image(url, use_container_width=True)
    else:
        h = int((width or 150) * 1.45)
        st.markdown(f"<div style='height:{h}px;background:#e9ecef;border-radius:6px;display:flex;"
                    f"align-items:center;justify-content:center;color:#868e96'>🎬</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ truy vấn
def dw_query(sql, params=None) -> pd.DataFrame:
    with psycopg2.connect(config.dw_dsn()) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def app_exec(sql, params=None):
    with psycopg2.connect(config.app_dsn()) as conn, conn.cursor() as cur:
        cur.execute(sql, params)


def app_query(sql, params=None) -> pd.DataFrame:
    with psycopg2.connect(config.app_dsn()) as conn:
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=600)
def movies() -> pd.DataFrame:
    return dw_query("""
        SELECT m.movie_id, m.title, m.year, m.poster_url, m.directors, m.runtime_minutes,
               string_agg(g.genre_name, ', ' ORDER BY g.genre_name) AS genres
        FROM dw.dim_movie m
        LEFT JOIN dw.bridge_movie_genre b USING (movie_key) LEFT JOIN dw.dim_genre g USING (genre_key)
        GROUP BY m.movie_key""").set_index("movie_id")


@st.cache_resource(show_spinner="Đang huấn luyện mô hình gợi ý từ kho dữ liệu ...")
def recommender(version: str) -> HybridRecommender:
    """Học độ tương đồng giữa các phim từ toàn bộ rating (~8 giây). Chỉ học lại mỗi ngày hoặc khi bấm nút:
    gợi ý cho từng user luôn đọc lịch sử MỚI NHẤT của user từ kho, nên rating vừa nạp có hiệu lực ngay,
    không cần học lại độ tương đồng."""
    emb = dw_query("SELECT m.movie_id, e.embedding::text AS v FROM dw.movie_embedding e JOIN dw.dim_movie m USING (movie_key)")
    vectors = {r.movie_id: np.array(json.loads(r.v), dtype=np.float32) for r in emb.itertuples()}
    train = dw_query("SELECT user_id, movie_id, rating FROM dw.fact_rating WHERE NOT is_deleted")
    return HybridRecommender(vectors).fit(train)


def model_version() -> str:
    return date.today().isoformat()


def encoder():
    if not embeddings.is_loaded():
        with st.spinner("Mô hình tìm kiếm đang tải nốt (chỉ lần đầu sau khi mở app) ..."):
            embeddings.model()
    return lambda texts: embeddings.encode(texts, kind="query")


def user_history(user_id: int) -> pd.DataFrame:
    return dw_query("""
        SELECT f.movie_id, f.rating, f.rated_at, s.source_name AS source
        FROM dw.fact_rating f JOIN dw.dim_source s USING (source_key)
        WHERE f.user_id = %s AND NOT f.is_deleted ORDER BY f.rated_at DESC""", (user_id,))


def recommend_for(user_id: int, alpha: float = DEMO_ALPHA, top_n: int = 5):
    hist = user_history(user_id)
    return recommender(model_version()).recommend(dict(zip(hist.movie_id, hist.rating)), alpha=alpha, top_n=top_n)


def poster_grid(recs, show_reason=True):
    cat = movies()
    cols = st.columns(len(recs) or 1)
    for col, r in zip(cols, recs):
        m = cat.loc[r.movie_id]
        with col:
            show_poster(m.poster_url)
            st.markdown(f"**{m.title}** ({m.year})")
            st.caption(m.genres or "")
            st.caption(f"điểm {r.score:.2f} · CF {r.cf:.2f} · nội dung {r.content:.2f}")
            if show_reason and r.because in cat.index:
                st.caption(f"Vì bạn thích *{cat.loc[r.because].title}*")


def mini_grid(movie_ids, highlight=()):
    cat = movies()
    cols = st.columns(len(movie_ids) or 1)
    for col, mid in zip(cols, movie_ids):
        m = cat.loc[mid]
        with col:
            show_poster(m.poster_url)
            st.markdown((":green-background[**MỚI**] " if mid in highlight else "") + f"**{m.title}**")


def start_journey(table: str, action: str, user_id: int, movie_id: int | None = None):
    """Ghi lại thay đổi vừa làm để panel bên phải theo dõi nó qua từng chặng."""
    prev = st.session_state.get("journey")
    ch = journey.Change(table, action, user_id, movie_id, datetime.now(timezone.utc))
    if table == "ratings":
        # Gợi ý "trước": giữ của lần thay đổi đầu tiên chưa vào kho, để so với "sau" khi pipeline xong.
        if prev and prev.table == "ratings" and prev.user_id == user_id and prev.dw is None and prev.recs_before:
            ch.recs_before = prev.recs_before
        else:
            ch.recs_before = [r.movie_id for r in recommend_for(user_id)]
    st.session_state["journey"] = ch


def step_line(done: bool, name: str, detail: str, at=None, waiting=False):
    icon = "✅" if done else ("⏳" if waiting else "▫️")
    when = f" · `{at.astimezone():%H:%M:%S}`" if done and at else ""
    st.markdown(f"{icon} **{name}**{when}  \n<span style='color:#6b7280;font-size:0.85em'>{detail}</span>",
                unsafe_allow_html=True)


@st.fragment(run_every=3)
def journey_panel():
    ch = st.session_state.get("journey")
    st.markdown("#### Hành trình của thay đổi vừa làm")
    if ch is None:
        st.caption("Chấm điểm, xóa hoặc đổi nghề ở bên trái để theo dõi thay đổi đi qua pipeline.")
        return
    if ch.dw is None:
        try:
            journey.advance(ch)
        except Exception as e:  # dịch vụ nào đó chưa sẵn sàng: lần làm mới sau thử lại
            st.caption(f"Đang chờ: {type(e).__name__}")
    k, b, a, d = ch.kafka, ch.bronze, ch.airflow, ch.dw
    step_line(True, "Postgres app", ch.action, ch.at)
    step_line(k is not None, "Kafka (Debezium đọc WAL)",
              f"{k['topic']} · op `{k['op']}` · partition {k['partition']} · offset {k['offset']}" if k
              else "chờ Debezium …", k and k["at"], waiting=k is None)
    step_line(b is not None, "MinIO bronze (consumer)",
              b["path"] if b else "chờ consumer gom micro-batch (≤ 10 giây) …",
              b and b["at"], waiting=k is not None and b is None)
    if a is None:
        a_detail, a_done = "chưa chạy — bấm **▶ Chạy pipeline ngay** bên dưới", False
    elif a["state"] == "success":
        a_detail, a_done = f"{a['run_id']} · {a['done']}/{a['total']} task xanh", True
    elif a["failed"]:
        a_detail, a_done = f"❌ lỗi ở {', '.join(a['failed'])}", False
    else:
        doing = f"đang chạy {a['running']}" if a["running"] else "đang hoàn tất"
        a_detail, a_done = f"{a['done']}/{a['total']} task xong · {doing}", False
    step_line(a_done, "Airflow movie_incremental", a_detail, a and a["at"], waiting=b is not None and not a_done)
    step_line(d is not None, "Kho dữ liệu", d["detail"] if d else "chờ nạp …", d and d["at"],
              waiting=a_done and d is None)
    if d is not None:
        secs = (d["at"] - ch.at).total_seconds()
        st.success(f"Thay đổi đã vào kho sau {secs:.0f} giây")
        if ch.table == "ratings" and ch.recs_before:
            if ch.recs_after is None:
                ch.recs_after = [r.movie_id for r in recommend_for(ch.user_id)]
            st.markdown(f"**Gợi ý cho user {ch.user_id} — trước**")
            mini_grid(ch.recs_before)
            st.markdown("**Sau** (phim mới xuất hiện được đánh dấu)")
            mini_grid(ch.recs_after, highlight=set(ch.recs_after) - set(ch.recs_before))


# ------------------------------------------------------------------ giao diện
st.title("🎬 Movie Platform")
tab_rec, tab_rate, tab_new, tab_search, tab_pipe = st.tabs(
    ["Gợi ý cho bạn", "Chấm điểm", "Người dùng mới", "Tìm phim theo mô tả", "Pipeline"])

with tab_rec:
    c1, c2 = st.columns([1, 2])
    user_id = c1.number_input("Mã người dùng", min_value=1, max_value=999999, value=1, step=1)
    alpha = c2.slider("α: trọng số CF (1 = chỉ CF như bản cũ, 0 = chỉ nội dung)", 0.0, 1.0, 0.7, 0.1)
    profile = dw_query("SELECT gender, age_group, occupation, valid_from FROM dw.dim_user "
                       "WHERE user_id = %s AND is_current", (int(user_id),))
    hist = user_history(int(user_id))
    if not profile.empty:
        p = profile.iloc[0]
        st.write(f"Giới tính **{p.gender}**, tuổi **{p.age_group}**, nghề **{p.occupation}** · "
                 f"đã chấm **{len(hist)}** phim ({(hist.source == 'app').sum()} trên app)")
    recs = recommend_for(int(user_id), alpha=alpha)
    poster_grid(recs)
    if st.button("Huấn luyện lại mô hình gợi ý (~8 giây)"):
        recommender.clear()
        st.rerun()
    with st.expander("Phim chấm gần đây"):
        cat = movies()
        h = hist.head(15).assign(title=lambda d: d.movie_id.map(cat.title))
        st.dataframe(h[["title", "rating", "rated_at", "source"]], hide_index=True, use_container_width=True)

with tab_rate:
    st.write("Thao tác ghi thẳng vào **database của app** (Postgres). Debezium bắt thay đổi qua WAL → "
             "Kafka → MinIO → Airflow nạp vào kho → gợi ý thay đổi. Panel bên phải theo dõi từng chặng.")
    cat = movies()
    left, right = st.columns([3, 2], gap="large")
    with left:
        c1, c2, c3 = st.columns([1, 1, 2], vertical_alignment="bottom")
        if "rate_user" not in st.session_state:
            st.session_state["rate_user"] = 1
        if c2.button("➕ Tạo người dùng mới", help="INSERT vào bảng users của app → CDC → dim_user. "
                                                  "Người mới chưa có lịch sử nên gợi ý thay đổi rõ sau khi chấm."):
            new_id = int(app_query("SELECT coalesce(max(user_id), 0) + 1 AS id FROM users").id[0])
            start_journey("users", f"tạo người dùng mới {new_id}", new_id)
            app_exec("INSERT INTO users (user_id, gender, age, occupation) VALUES (%s, 'M', 25, 4)", (new_id,))
            st.session_state["rate_user"] = new_id
        rate_user = int(c1.number_input("Mã người dùng ", min_value=1, max_value=999999, step=1, key="rate_user"))
        query = c3.text_input("Tìm tên phim", "Toy Story")
        found = cat[cat.title.str.contains(query, case=False, na=False)].head(6) if query else cat.head(0)
        # Danh sách dài/ngắn thay đổi nằm trong container riêng: số phần tử ở cấp ngoài cố định,
        # tránh lỗi Streamlit hiện trùng phần tử cũ khi panel bên phải tự làm mới.
        movie_list = st.container()
        for mid, m in found.iterrows():
            a, b, c, d = movie_list.columns([1, 4, 2, 1])
            with a:
                show_poster(m.poster_url, width=60)
            b.markdown(f"**{m.title}** ({m.year})  \n{m.genres}")
            stars = c.select_slider("Số sao", [1, 2, 3, 4, 5], value=5, key=f"s{mid}")
            if d.button("Chấm", key=f"b{mid}"):
                start_journey("ratings", f"user {rate_user} chấm {stars}★ {m.title}", rate_user, int(mid))
                app_exec("""INSERT INTO ratings (user_id, movie_id, rating) VALUES (%s, %s, %s)
                            ON CONFLICT (user_id, movie_id) DO UPDATE SET rating = EXCLUDED.rating""",
                         (rate_user, int(mid), int(stars)))

        st.divider()
        st.markdown("**Rating của người dùng này trên app** "
                    "(xóa → CDC gửi sự kiện `op: d` → kho đánh dấu `is_deleted`)")
        app_rows = app_query("SELECT movie_id, rating, updated_at FROM ratings WHERE user_id = %s "
                             "ORDER BY updated_at DESC LIMIT 10", (rate_user,))
        rating_list = st.container()
        if app_rows.empty:
            rating_list.caption("Chưa có rating nào trên app.")
        for r in app_rows.itertuples():
            a, b, c = rating_list.columns([5, 2, 1])
            title = cat.loc[r.movie_id].title if r.movie_id in cat.index else str(r.movie_id)
            a.write(title)
            b.write(f"{r.rating}★ · {r.updated_at.to_pydatetime().astimezone():%H:%M:%S}")
            if c.button("Xóa", key=f"del{r.movie_id}"):
                start_journey("ratings", f"user {rate_user} xóa rating {title}", rate_user, int(r.movie_id))
                app_exec("DELETE FROM ratings WHERE user_id = %s AND movie_id = %s", (rate_user, int(r.movie_id)))
                st.rerun()

        st.divider()
        st.markdown("**Đổi nghề nghiệp** (UPDATE bảng users → CDC → kho giữ lịch sử theo **SCD loại 2**)")
        cur_occ = app_query("SELECT occupation FROM users WHERE user_id = %s", (rate_user,))
        o1, o2 = st.columns([3, 1])
        new_occ = o1.selectbox("Nghề mới", range(len(OCCUPATIONS)), format_func=lambda i: OCCUPATIONS[i],
                               index=int(cur_occ.occupation[0]) if not cur_occ.empty else 0)
        if o2.button("Cập nhật"):
            start_journey("users", f"user {rate_user} đổi nghề thành {OCCUPATIONS[new_occ]}", rate_user)
            app_exec("UPDATE users SET occupation = %s WHERE user_id = %s", (int(new_occ), rate_user))

    with right:
        with st.container(border=True):
            journey_panel()
        if st.button("▶ Chạy pipeline ngay (Airflow: movie_incremental)", type="primary",
                     use_container_width=True):
            try:
                st.success(f"Đã kích hoạt {journey.trigger_pipeline()}")
            except Exception as e:
                st.error(f"Không gọi được Airflow: {e}")

with tab_new:
    st.write("Người dùng mới chưa có lịch sử: chọn vài phim yêu thích, mô hình gợi ý ngay "
             "(minh họa bài toán **cold-start**).")
    cat = movies()
    options = cat.sort_values("title").apply(lambda m: f"{m.title} ({m.year})", axis=1)
    picked = st.multiselect("Phim bạn thích", options.index, format_func=lambda i: options[i], max_selections=5)
    if picked:
        model = recommender(model_version())
        cols = st.columns(2)
        with cols[0]:
            st.subheader("Chỉ CF (bản cũ)")
            poster_grid(model.recommend({m: 5 for m in picked}, alpha=1.0, top_n=5))
        with cols[1]:
            st.subheader("Hybrid (CF + nội dung)")
            poster_grid(model.recommend({m: 5 for m in picked}, alpha=0.5, top_n=5))

with tab_search:
    st.write("Gõ mô tả bằng tiếng Việt hoặc tiếng Anh. Câu hỏi được biến thành vector rồi tìm phim gần nhất "
             "trong kho bằng **pgvector** (cosine).")
    text = st.text_input("Mô tả", "phim hoạt hình về đồ chơi biết nói")
    if text:
        v = encoder()([text])[0]
        vec = "[" + ",".join(f"{x:.6f}" for x in v) + "]"
        res = dw_query("""
            SELECT m.movie_id, m.title, m.year, m.poster_url, 1 - (e.embedding <=> %s::vector) AS similarity,
                   left(e.doc, 300) AS doc
            FROM dw.movie_embedding e JOIN dw.dim_movie m USING (movie_key)
            ORDER BY e.embedding <=> %s::vector LIMIT 8""", (vec, vec))
        for r in res.itertuples():
            a, b = st.columns([1, 6])
            with a:
                show_poster(r.poster_url, width=80)
            b.markdown(f"**{r.title}** ({r.year}) — độ giống {r.similarity:.2f}  \n{r.doc}…")

with tab_pipe:
    st.subheader("Lần chạy gần nhất của từng bước")
    st.dataframe(dw_query("""
        SELECT DISTINCT ON (step) step, status, started_at, finished_at - started_at AS duration, rows_in, rows_out
        FROM etl.pipeline_run ORDER BY step, run_id DESC"""), hide_index=True, use_container_width=True)
    st.subheader("Rating trong kho theo nguồn")
    st.dataframe(dw_query("""
        SELECT s.source_name, count(*) AS ratings, sum(f.is_deleted::int) AS deleted, max(f.loaded_at) AS last_loaded
        FROM dw.fact_rating f JOIN dw.dim_source s USING (source_key) GROUP BY 1"""), hide_index=True)
    st.subheader("Rating mới nhất từ app (đã qua CDC)")
    st.dataframe(dw_query("""
        SELECT f.user_id, m.title, f.rating, f.is_deleted, f.changed_at, f.loaded_at
        FROM dw.fact_rating f JOIN dw.dim_movie m USING (movie_key)
        WHERE f.source_key = 2 ORDER BY f.changed_at DESC LIMIT 10"""), hide_index=True, use_container_width=True)
    st.markdown(f"[Airflow]({AIRFLOW}) · [Kafka UI](http://localhost:8080) · "
                "[MinIO](http://localhost:9001) · [Superset](http://localhost:8089)")
