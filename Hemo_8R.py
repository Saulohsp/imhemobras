# Libraries
import re
import datetime as dt
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import altair as alt

# -------------------------------------------------------------------------------------------------
# Page configuration
st.set_page_config(page_title="I.M", layout="wide")

# -------------------------------------------------------------------------------------------------

# Título da página selecionada
st.title("Hemo 8R")

# -------------------------------------------------------------------------------------------------

# Função para carregar e tratar o CSV - Serviços de saúde

@st.cache_data
def load_data(path_csv: str):
    # Lê como texto para tratar separador de milhar usando ';'
    df = pd.read_csv(path_csv, sep=";", dtype=str)

    ui_cols = ["250 UI", "500 UI", "1000 UI", "1500 UI", "Total Geral"]
    base_cols = ["Período de saída", "Serviço de Saúde"] + ui_cols
    df = df[base_cols]

    # Normaliza números removendo pontos (ex.: "3.100" -> 3100)
    for c in ui_cols:
        df[c] = (
            df[c]
            .fillna("0")
            .str.replace(".", "", regex=False)
            .str.strip()
        )
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # Converte "janeiro/19" -> 2019-01-01 (primeiro dia do mês)
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
        "outubro": 10, "novembro": 11, "dezembro": 12
    }

    def parse_periodo(s):
        s = str(s).strip().lower()
        m = re.match(r"([a-zç]+)\/?(\d{2}|\d{4})", s)
        if not m:
            return pd.NaT
        mon = m.group(1).replace("ç", "c")
        ano = int(m.group(2))
        ano = 2000 + ano if ano < 100 else ano
        mes = meses.get(mon)
        if not mes:
            return pd.NaT
        return dt.date(ano, mes, 1)

    df["periodo"] = df["Período de saída"].apply(parse_periodo)
    df = df.dropna(subset=["periodo"]).copy()

    return df, ui_cols

# -------------------------------------------------------------------------------------------------

# Função para carregar CSV do Ministério da Saúde (ano x quantidade)

@st.cache_data
def load_ms_data(path_csv: str = "hemo8R_MS.csv"):
    df = pd.read_csv(path_csv, sep=";", dtype=str)
    df = df.rename(columns={"ano": "Ano", "quantidade": "Quantidade"})
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
    df = df.dropna().sort_values("Ano")
    return df

# -------------------------------------------------------------------------------------------------

# Gráfico: Distribuição do Hemo 8R (Ministério da Saúde)

st.subheader("Distribuição do Hemo 8R — Ministério da Saúde")

try:
    df_ms = load_ms_data("hemo8R_MS.csv")
except Exception as e:
    st.warning(f"Erro ao carregar hemo8R_MS.csv: {e}")
    df_ms = pd.DataFrame()

if not df_ms.empty:
    # KPIs simples
    c1, c2, c3 = st.columns(3)
    c1.metric("De", str(df_ms["Ano"].min()))
    c2.metric("Até", str(df_ms["Ano"].max()))
    c3.metric("Total distribuído (UI)", f"{int(df_ms['Quantidade'].sum()):,}".replace(",", "."))

    # Gráfico de barras
    chart_ms = (
        alt.Chart(df_ms)
        .mark_bar()
        .encode(
            x=alt.X("Ano:O", title="Ano"),
            y=alt.Y("Quantidade:Q", title="Quantidade (UI)", axis=alt.Axis(format=",.0f")),
            tooltip=[alt.Tooltip("Ano:O"), alt.Tooltip("Quantidade:Q", format=",.0f")]
        )
        .properties(height=400)
    )
    st.altair_chart(chart_ms, use_container_width=True)

    with st.expander("Ver dados do Ministério da Saúde"):
        st.dataframe(df_ms, use_container_width=True)
else:
    st.info("Nenhum dado disponível do Ministério da Saúde.")


# Arquivo já está na mesma pasta do main.py
DATA_PATH = "historico_hemo8r.csv"  # ajuste para o nome EXATO do seu arquivo

try:
    df, ui_cols = load_data(DATA_PATH)
except Exception as e:
    st.error(f"Erro ao carregar {DATA_PATH}: {e}")
    st.stop()

st.subheader("Distribuição do Hemo 8R — Serviços de saúde")

# KPIs
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("De", df["periodo"].min().strftime("%b/%Y"))
col2.metric("Até", df["periodo"].max().strftime("%b/%Y"))

servicos = f"{df['Serviço de Saúde'].nunique():,}".replace(",", ".")
volume_total = f"{int(df['Total Geral'].sum()):,}".replace(",", ".")
registros = f"{len(df):,}".replace(",", ".")

col3.metric("Serviços distintos", servicos)
col4.metric("Volume total (UI)", volume_total)
col5.metric("Registros", registros)

# Gráfico 1: Série temporal por UI (mensal)
st.subheader("Evolução mensal por UI")
monthly = df.groupby("periodo")[ui_cols].sum().sort_index()
st.line_chart(monthly)

# Gráfico 2: Ranking por serviço (Total acumulado)
st.subheader("Top serviços por volume total (UI)")
top_n = st.slider("Quantos serviços exibir?", 5, 31, 15, key="n_top_hemo")
rank = (
    df.groupby("Serviço de Saúde")["Total Geral"]
    .sum()
    .reset_index()
    .sort_values("Total Geral", ascending=False)  # ordena pelos valores
    .head(top_n)
)
chart = (
    alt.Chart(rank)
    .mark_bar()
    .encode(
        x=alt.X("Serviço de Saúde:N", sort=rank["Serviço de Saúde"].tolist(), title="Serviço"),
        y=alt.Y("Total Geral:Q", title="Volume total (UI)", axis=alt.Axis(format=",.0f")),
        tooltip=["Serviço de Saúde", alt.Tooltip("Total Geral:Q", format=",.0f")]
    )
    .properties(height=400)
)
st.altair_chart(chart, use_container_width=True)


# Tabela
with st.expander("Ver amostra dos dados tratados"):
    st.dataframe(df, use_container_width=True)