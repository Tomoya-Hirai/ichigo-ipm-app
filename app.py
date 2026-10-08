
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="イチゴ総合防除ナビ",
    page_icon="🍓",
    layout="centered",
)

DATA_FILE = Path(__file__).parent / "IPMアプリ＿データ.xlsx"

@st.cache_data
def load_ipm_data(path):
    # Excelの「オリジナル」シートを、病害虫ごとの6列セットとして読み込む
    raw = pd.read_excel(path, sheet_name="オリジナル", header=None)

    # 2行目（Excel上では2行目）に「病害」「害虫」が入っている
    header = raw.iloc[1].fillna("")

    records = []

    # 6列セット：対象、分類、防除技術、時期、IPM段階
    # 各セットの先頭列を、2行目の「病害」「害虫」から探す
    start_cols = []
    for col in range(len(header)):
        if str(header.iloc[col]).strip() in ["病害", "害虫"]:
            start_cols.append(col)

    for start in start_cols:
        # 期待する列構造
        if start + 5 >= raw.shape[1]:
            continue

        for row in range(2, raw.shape[0]):
            target = raw.iloc[row, start]
            category = raw.iloc[row, start + 1]
            method = raw.iloc[row, start + 2]
            timing = raw.iloc[row, start + 3]
            stage = raw.iloc[row, start + 4]

            if pd.isna(target) or str(target).strip() == "":
                continue
            if pd.isna(method) or str(method).strip() == "":
                continue

            records.append({
                "種類": "病害" if str(header.iloc[start]).strip() == "病害" else "害虫",
                "病害虫": str(target).strip(),
                "防除分類": "" if pd.isna(category) else str(category).strip(),
                "防除技術": str(method).strip(),
                "時期": "" if pd.isna(timing) else str(timing).strip(),
                "IPM段階": "" if pd.isna(stage) else str(stage).strip(),
            })

    df = pd.DataFrame(records).drop_duplicates().reset_index(drop=True)
    return df


st.title("🍓 イチゴ総合防除ナビ")
st.write("病害虫を選択すると、登録されている総合防除方法を表示します。")

if not DATA_FILE.exists():
    st.error(
        "「IPMアプリ＿データ.xlsx」が見つかりません。"
        "app.pyと同じフォルダに置いてください。"
    )
    st.stop()

df = load_ipm_data(DATA_FILE)

if df.empty:
    st.error("Excelから防除データを読み込めませんでした。")
    st.stop()

# --- 選択 ---
kind = st.radio(
    "① 対象を選択してください",
    ["病害", "害虫"],
    horizontal=True,
)

targets = sorted(df.loc[df["種類"] == kind, "病害虫"].unique())

target = st.selectbox(
    "② 病害虫を選択してください",
    targets,
)

result = df[(df["種類"] == kind) & (df["病害虫"] == target)].copy()

st.divider()

st.subheader(f"③ {target} の総合防除方法")

# 分類ごとに表示
order = ["耕種的防除", "物理的防除", "生物的防除", "化学的防除"]

shown = set()

for category in order:
    rows = result[result["防除分類"] == category]

    if rows.empty:
        continue

    shown.add(category)
    st.markdown(f"### {category}")

    for _, row in rows.iterrows():
        st.markdown(f"**・{row['防除技術']}**")

        details = []
        if row["時期"]:
            details.append(f"実施時期：{row['時期']}")
        if row["IPM段階"]:
            details.append(f"段階：{row['IPM段階']}")

        if details:
            st.caption(" / ".join(details))

# 想定外の防除分類も表示
other = result[~result["防除分類"].isin(shown)]
if not other.empty:
    st.markdown("### その他")
    for _, row in other.iterrows():
        st.markdown(f"**・{row['防除技術']}**")
        if row["時期"] or row["IPM段階"]:
            st.caption(
                f"実施時期：{row['時期']} / 段階：{row['IPM段階']}"
            )

st.divider()

st.caption(
    "※本アプリは「総合防除実践マニュアル」の情報を検索・表示する試作版です。"
    "病害虫の診断や、農薬の使用可否を決定するものではありません。"
    "実際の防除では、地域の指導機関・登録情報・最新の使用基準等を確認してください。"
)

with st.expander("📊 読み込んでいるデータを確認"):
    st.dataframe(
        result[["種類", "病害虫", "防除分類", "防除技術", "時期", "IPM段階"]],
        use_container_width=True,
        hide_index=True,
    )
