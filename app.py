import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="イチゴ総合防除ナビ", page_icon="🍓", layout="wide")

# 防除カテゴリーごとのボタン色
st.markdown(
    """
    <style>
    [class*="st-key-cat_orange"] button {
        background-color: #F39C12 !important;
        border-color: #F39C12 !important;
        color: white !important;
    }
    [class*="st-key-cat_green"] button {
        background-color: #239B56 !important;
        border-color: #239B56 !important;
        color: white !important;
    }
    [class*="st-key-cat_red"] button {
        background-color: #D64545 !important;
        border-color: #D64545 !important;
        color: white !important;
    }
    [class*="st-key-cat_blue"] button {
        background-color: #2878C8 !important;
        border-color: #2878C8 !important;
        color: white !important;
    }
    [class*="st-key-cat_orange"] button:hover,
    [class*="st-key-cat_green"] button:hover,
    [class*="st-key-cat_red"] button:hover,
    [class*="st-key-cat_blue"] button:hover {
        filter: brightness(0.90);
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_FILE = Path(__file__).parent / "IPMアプリ＿データ.xlsx"

STAGES = ["環境整備", "親株定植・育苗", "本圃準備・定植", "生育・収穫", "栽培後（片付け等）"]
CATEGORY_ORDER = ["耕種的防除", "物理的防除", "生物的防除", "化学的防除"]

@st.cache_data
def load_ipm_data(path):
    raw = pd.read_excel(path, sheet_name="オリジナル", header=None)
    header = raw.iloc[1].fillna("")
    records = []
    for col in range(len(header)):
        kind = str(header.iloc[col]).strip()
        if kind not in ["病害", "害虫"]:
            continue
        for row in range(2, raw.shape[0]):
            target = raw.iloc[row, col]
            method = raw.iloc[row, col + 2] if col + 2 < raw.shape[1] else None
            if pd.isna(target) or str(target).strip() == "" or pd.isna(method) or str(method).strip() == "":
                continue
            def val(offset):
                x = raw.iloc[row, col + offset]
                return "" if pd.isna(x) else str(x).strip()
            records.append({
                "種類": kind,
                "病害虫": str(target).strip(),
                "防除分類": val(1),
                "防除技術": val(2),
                "時期": val(3),
                "IPM段階": val(4),
            })
    return pd.DataFrame(records).drop_duplicates().reset_index(drop=True)

# 現時点で説明内容を用意できている技術のみ詳細説明を掲載
METHOD_DETAILS = {
    "生物農薬の利用（微生物製剤）": {
        "分類": "生物的防除",
        "概要": "微生物を利用した農薬（微生物製剤）を活用して、病害の発生を抑える防除方法です。化学農薬だけに頼らず、耕種的防除や物理的防除などと組み合わせて総合的に管理します。",
        "対象": "うどんこ病、灰色かび病",
        "確認事項": [
            "対象作物・対象病害に適用のある製剤を選びます。",
            "製品ラベルや最新の農薬登録情報で、使用時期、使用量、使用方法、使用回数を確認します。",
            "製剤によって使用条件や効果を発揮しやすい環境が異なるため、製品ごとの説明に従います。",
            "圃場の観察やほかの防除方法と組み合わせて管理します。",
        ],
        "根拠": "アップロードされたExcelでは、うどんこ病・灰色かび病の防除技術としてこの方法が登録されています。微生物の種類、製剤名、具体的な使用条件まではExcelに記載されていないため、製剤固有の条件は記載していません。",
    }
}

def normalize(text):
    return str(text).replace("\n", "").replace(" ", "").replace("　", "").replace("（", "(").replace("）", ")")

def display_method_name(method):
    return " ".join(str(method).split())

def open_detail(row):
    method = row["防除技術"]
    normalized = normalize(method)
    if "生物農薬の利用" in normalized and "微生物製剤" in normalized:
        key = "生物農薬の利用（微生物製剤）"
    else:
        key = method
    st.session_state["selected_method"] = key
    st.session_state["selected_original_method"] = method
    st.session_state["selected_target"] = row["病害虫"]
    st.session_state["selected_kind"] = row["種類"]
    st.session_state["selected_category"] = row["防除分類"]
    st.session_state["selected_timing"] = row["時期"]
    st.session_state["selected_stage"] = row["IPM段階"]
    st.session_state["page"] = "detail"



def show_calendar(df):
    st.title("🍓 イチゴ総合防除ナビ")
    st.subheader("総合防除カレンダー")
    st.write("病害虫名と表示対象を選択し、確認したい防除技術のボタンを押してください。")

    # ① 表示対象の種類と病害虫名を選ぶボックス
    kind = st.radio(
        "表示する対象",
        ["すべて", "病害", "害虫"],
        horizontal=True,
        key="calendar_kind",
    )

    if kind == "すべて":
        kind_view = df.copy()
    else:
        kind_view = df[df["種類"] == kind].copy()

    target_names = sorted(kind_view["病害虫"].dropna().astype(str).unique().tolist())
    target_options = ["すべて"] + target_names

    selected_target = st.selectbox(
        "病害虫名を選択",
        target_options,
        index=0,
        key="calendar_target_name",
        help="「すべて」を選ぶと、選択中の表示対象を一つのカレンダーにまとめて表示します。",
    )

    if selected_target == "すべて":
        view = kind_view
    else:
        view = kind_view[kind_view["病害虫"] == selected_target].copy()

    st.caption(
        "※列はExcelの「時期」欄にある栽培段階をもとにしています。"
        "月・実施時期の情報は各防除技術の下に表示します。"
    )

    # カレンダーのヘッダー
    header_cols = st.columns([1.25, 1, 1, 1, 1, 1])
    header_cols[0].markdown("**病害虫名**")
    for i, stage in enumerate(STAGES, start=1):
        header_cols[i].markdown(f"**{stage}**")

    st.divider()

    # ② 「すべて」の場合も病害虫ごとの行を同じ表に並べて一体表示
    targets = (
        view[["種類", "病害虫"]]
        .drop_duplicates()
        .sort_values(["種類", "病害虫"])
        .reset_index(drop=True)
    )

    if targets.empty:
        st.info("選択した条件に該当する防除データはありません。")
        return

    for _, target_row in targets.iterrows():
        target_kind = target_row["種類"]
        target_name = target_row["病害虫"]
        records = view[
            (view["種類"] == target_kind) &
            (view["病害虫"] == target_name)
        ]

        row_cols = st.columns([1.25, 1, 1, 1, 1, 1])
        with row_cols[0]:
            kind_label = "病害" if target_kind == "病害" else "害虫"
            st.markdown(f"**{target_name}**")
            st.caption(kind_label)

        for i, stage in enumerate(STAGES, start=1):
            with row_cols[i]:
                if stage.startswith("栽培後"):
                    matches = records[
                        records["時期"].str.contains("栽培後", na=False)
                    ]
                else:
                    matches = records[
                        records["時期"].str.contains(stage, na=False)
                    ]

                if matches.empty:
                    st.caption("—")
                else:
                    for idx, row in matches.iterrows():
                        label = display_method_name(row["防除技術"])
                        if len(label) > 30:
                            label = label[:29] + "…"

                        category_colors = {
                            "耕種的防除": "orange",
                            "生物的防除": "green",
                            "物理的防除": "red",
                            "化学的防除": "blue",
                        }
                        color_key = category_colors.get(row["防除分類"], "blue")
                        # 色分け用コンテナ内にボタンを置き、既存のクリック動作を維持
                        with st.container(key=f"cat_{color_key}_{target_kind}_{idx}"):
                            if st.button(
                                label,
                                key=f"cal_{target_kind}_{target_name}_{stage}_{idx}",
                                use_container_width=True,
                                help=f"{row['防除分類']}｜{row['時期']}",
                            ):
                                open_detail(row)
                                st.rerun()

                        st.caption(
                            f"{row['防除分類']}｜"
                            f"{row['時期'].replace(chr(10), ' ')}"
                        )

        st.divider()

    st.caption(
        "※このカレンダーは登録済みExcelデータを栽培段階別に整理した試作表示です。"
        "栽培暦は地域・作型・栽培条件により異なるため、実際の防除では地域の指導機関の情報も確認してください。"
    )
    with st.expander("📊 読み込んでいるデータを確認"):
        st.dataframe(df, use_container_width=True, hide_index=True)


def show_detail():
    key = st.session_state.get("selected_method", "")
    original = st.session_state.get("selected_original_method", key)
    info = METHOD_DETAILS.get(key)
    st.title("防除技術の詳細")
    st.header(display_method_name(original))
    st.markdown(f"**対象：** {st.session_state.get('selected_target', '')}")
    st.markdown(f"**防除分類：** {st.session_state.get('selected_category', '')}")
    if st.session_state.get("selected_timing"):
        st.markdown(f"**実施時期：** {st.session_state['selected_timing']}")
    if st.session_state.get("selected_stage"):
        st.markdown(f"**IPM段階：** {st.session_state['selected_stage']}")
    st.divider()
    if info:
        st.subheader("防除方法の概要")
        st.write(info["概要"])
        st.subheader("Excelに登録されている対象")
        st.write(info["対象"])
        st.subheader("実施時の確認事項")
        for item in info["確認事項"]:
            st.markdown(f"- {item}")
        st.info(info["根拠"])
    else:
        st.info("この防除技術の詳細説明は、まだ登録されていません。現在はExcelに記載された防除技術名・分類・時期を表示しています。詳細説明は技術ごとに順次追加できます。")
    st.caption("※農薬を使用する場合は、必ず製品ラベルと最新の農薬登録情報で対象作物・対象病害虫・使用条件を確認してください。")
    if st.button("← カレンダーに戻る", type="primary"):
        st.session_state["page"] = "calendar"
        st.rerun()

if not DATA_FILE.exists():
    st.error("『IPMアプリ＿データ.xlsx』が見つかりません。app.pyと同じフォルダに置いてください。")
    st.stop()

df = load_ipm_data(DATA_FILE)
if df.empty:
    st.error("Excelから防除データを読み込めませんでした。")
    st.stop()
if "page" not in st.session_state:
    st.session_state["page"] = "calendar"
if st.session_state["page"] == "detail":
    show_detail()
else:
    show_calendar(df)
