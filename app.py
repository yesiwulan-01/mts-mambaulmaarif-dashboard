import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
import hashlib

st.set_page_config(page_title="MTs Mamba'ul Ma'arif", layout="wide")

# ===============================
# STYLE MODERN (CSS)
# ===============================
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #1e3c72, #2a5298);
    color: white;
}
.block-container {
    padding-top: 2rem;
}
h1, h2, h3 {
    color: white;
}
.stButton>button {
    background: linear-gradient(90deg, #ff9966, #ff5e62);
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-weight: bold;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# LOGIN MULTI ROLE
# ===============================
users = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "guru": hashlib.sha256("guru123".encode()).hexdigest(),
    "bk": hashlib.sha256("bk123".encode()).hexdigest()
}

def login():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in users and users[username] == hashlib.sha256(password.encode()).hexdigest():
            st.session_state["login"] = True
            st.session_state["role"] = username
        else:
            st.sidebar.error("Login gagal")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

st.sidebar.success(f"Login sebagai: {st.session_state['role']}")

# ===============================
# HEADER + LOGO
# ===============================
col_logo, col_title = st.columns([1,4])
with col_logo:
    st.image("assets/logo.png", width=100)
with col_title:
    st.markdown("<h1>🎓 MTs Mamba'ul Ma'arif</h1>", unsafe_allow_html=True)

st.divider()

# ===============================
# UPLOAD FILE
# ===============================
uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    angkatan_list = sorted(df["Angkatan"].unique())
    selected_angkatan = st.sidebar.multiselect(
        "Pilih Angkatan",
        angkatan_list,
        default=angkatan_list
    )

    df = df[df["Angkatan"].isin(selected_angkatan)].copy()

    # ===============================
    # ROLE-BASED MENU
    # ===============================
    if st.session_state["role"] == "admin":
        menu_options = [
            "Dashboard Utama",
            "Perbandingan Antar Angkatan",
            "Prediksi Kelulusan",
            "Heatmap Semester",
            "Analisis Per Siswa"
        ]
    elif st.session_state["role"] == "guru":
        menu_options = [
            "Dashboard Utama",
            "Perbandingan Antar Angkatan",
            "Analisis Per Siswa"
        ]
    else:  # BK
        menu_options = [
            "Dashboard Utama",
            "Prediksi Kelulusan",
            "Analisis Per Siswa"
        ]

    menu = st.sidebar.radio("Menu Navigasi", menu_options)

    # =====================================
    # DASHBOARD UTAMA
    # =====================================
    if menu == "Dashboard Utama":

        st.subheader("📊 Ringkasan Akademik")

        col1, col2, col3 = st.columns(3)
        col1.metric("Jumlah Siswa", len(df))
        col2.metric("Rata-rata Akademik", round(df["Rata_6_Semester"].mean(),2))
        col3.metric("Nilai Tertinggi", df["Rata_6_Semester"].max())

        st.divider()

        # SKOR RISIKO VISUAL (GAUGE)
        st.subheader("⚠ Skor Risiko Akademik Rata-rata")

        df["Trend"] = df["S6"] - df["S1"]
        df["Risk_Score"] = (
            (df["Rata_6_Semester"] < 75).astype(int)*3 +
            (df["Trend"] < -3).astype(int)*2
        )

        avg_risk = df["Risk_Score"].mean()

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_risk,
            title={'text': "Rata-rata Skor Risiko"},
            gauge={
                'axis': {'range': [0, 5]},
                'bar': {'color': "red"},
                'steps': [
                    {'range': [0,2], 'color': "green"},
                    {'range': [2,4], 'color': "yellow"},
                    {'range': [4,5], 'color': "red"},
                ]
            }
        ))

        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.subheader("📌 Kategori Risiko Akademik")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.success("🟢 Risiko Rendah (0 – 2)")
            st.write("Performa akademik stabil dan dalam kondisi aman.")

        with col2: 
            st.warning("🟡 Risiko Sedang (2 – 4)")
            st.write("Perlu monitoring dan perhatian berkala.")

        with col3:
            st.error("🔴 Risiko Tinggi (4 – 5)")
            st.write("Memerlukan pendampingan dan evaluasi khusus.")

    # =====================================
    # PERBANDINGAN ANGKATAN
    # =====================================
    elif menu == "Perbandingan Antar Angkatan":

        st.subheader("📈 Perbandingan Antar Angkatan")

        perbandingan = df.groupby("Angkatan")["Rata_6_Semester"].mean().reset_index()

        fig = px.bar(perbandingan, x="Angkatan", y="Rata_6_Semester",
                     color="Angkatan", text_auto=True)

        st.plotly_chart(fig, use_container_width=True)

        if len(perbandingan) >= 2:
            terbaik = perbandingan.loc[
                perbandingan["Rata_6_Semester"].idxmax()
            ]
            st.success(
                f"Angkatan {terbaik['Angkatan']} memiliki performa terbaik."
            )

    # =====================================
    # PREDIKSI KELULUSAN
    # =====================================
    elif menu == "Prediksi Kelulusan":

        st.subheader("🎯 Prediksi Kelulusan")

        df["Lulus_Label"] = np.where(df["Rata_6_Semester"] >= 75, 1, 0)
        features = df[["S1","S2","S3","S4","S5","S6"]]

        model = RandomForestClassifier(random_state=42)
        model.fit(features, df["Lulus_Label"])

        df["Prediksi"] = model.predict(features)

        df["Status"] = df["Prediksi"].apply(
            lambda x: "Berpotensi Lulus" if x == 1 else "Perlu Pendampingan"
        )

        st.dataframe(df[["Nama","Rata_6_Semester","Status"]])

    # =====================================
    # HEATMAP
    # =====================================
    elif menu == "Heatmap Semester":

        st.subheader("🔥 Heatmap Semester")

        heatmap_df = df[["Nama","S1","S2","S3","S4","S5","S6"]].head(25)
        heatmap_df = heatmap_df.set_index("Nama")

        fig = px.imshow(heatmap_df,
                        labels=dict(x="Semester", y="Siswa", color="Nilai"),
                        aspect="auto")

        st.plotly_chart(fig, use_container_width=True)

    # =====================================
    # ANALISIS SISWA
    # =====================================
    elif menu == "Analisis Per Siswa":

        st.subheader("📈 Analisis Per Siswa")

        selected_student = st.selectbox("Pilih Siswa", df["Nama"].unique())
        student = df[df["Nama"] == selected_student]

        trend_df = pd.DataFrame({
            "Semester": ["S1","S2","S3","S4","S5","S6"],
            "Nilai": [
                student["S1"].values[0],
                student["S2"].values[0],
                student["S3"].values[0],
                student["S4"].values[0],
                student["S5"].values[0],
                student["S6"].values[0],
            ]
        })

        fig = px.line(trend_df, x="Semester", y="Nilai", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        if trend_df["Nilai"].iloc[-1] > trend_df["Nilai"].iloc[0]:
            st.success("Performa siswa meningkat.")
        else:
            st.warning("Performa siswa cenderung menurun.")

else:
    st.info("Silakan upload file Excel terlebih dahulu.")