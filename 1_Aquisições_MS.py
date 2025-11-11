import pandas as pd
import streamlit as st
import altair as alt

# --------------------------------------------------------------------------------
# Configuração da página
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Coagulopatias",
    layout="wide"
)

st.title("Aquisições de Medicamentos para Coagulopatias")

# --------------------------------------------------------------------------------
# Função para carregar e tratar os dados
# --------------------------------------------------------------------------------
@st.cache_data
def load_coagulopatias_data(path_csv: str = "medicamentos_coagulopatias.csv"):
    # Lê como texto para garantir controle do parsing
    df_raw = pd.read_csv(path_csv, sep=";", dtype=str)

    # Identifica colunas de ano (tudo que não for 'medicamento')
    year_cols = [c for c in df_raw.columns if c.lower() != "medicamento"]

    # Transforma de formato wide (uma coluna por ano) para long (linhas ano a ano)
    df = df_raw.melt(
        id_vars="medicamento",
        value_vars=year_cols,
        var_name="Ano",
        value_name="Quantidade"
    )

    # Limpa ano
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")

    # Limpa quantidade:
    # - troca separador de milhar "." (se existir)
    # - troca vírgula por ponto (caso exista decimal)
    # - converte para numérico, NaN -> 0
    df["Quantidade"] = (
        df["Quantidade"]
        .fillna("0")
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)

    # Remove linhas sem ano válido
    df = df.dropna(subset=["Ano"])

    # Garante tipo int para Ano quando possível
    df["Ano"] = df["Ano"].astype(int)

    # Ordena para facilitar gráficos
    df = df.sort_values(["Ano", "medicamento"])

    return df


# --------------------------------------------------------------------------------
# Carregamento dos dados
# --------------------------------------------------------------------------------
try:
    df = load_coagulopatias_data("medicamentos_coagulopatias.csv")
except Exception as e:
    st.error(f"Erro ao carregar medicamentos_coagulopatias.csv: {e}")
    st.stop()

if df.empty:
    st.warning("Nenhum dado disponível na planilha de medicamentos para coagulopatias.")
    st.stop()

# --------------------------------------------------------------------------------
# Filtros (barra lateral)
# --------------------------------------------------------------------------------
st.sidebar.header("Filtros")

anos_disponiveis = sorted(df["Ano"].unique())
ano_min, ano_max = int(min(anos_disponiveis)), int(max(anos_disponiveis))

intervalo_anos = st.sidebar.slider(
    "Selecione o intervalo de anos",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1
)

df_filtrado = df[
    (df["Ano"] >= intervalo_anos[0]) &
    (df["Ano"] <= intervalo_anos[1])
].copy()

# --------------------------------------------------------------------------------
# KPIs
# --------------------------------------------------------------------------------
total_geral = int(df_filtrado["Quantidade"].sum())
num_medicamentos = df_filtrado["medicamento"].nunique()
num_anos = df_filtrado["Ano"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Período analisado", f"{intervalo_anos[0]} - {intervalo_anos[1]}")
col2.metric("Medicamentos distintos", str(num_medicamentos))
col3.metric("Total adquirido (todas apresentações)", f"{total_geral:,}".replace(",", "."))

st.markdown("---")

# --------------------------------------------------------------------------------
# Gráfico 1: Total anual de todos os medicamentos
# --------------------------------------------------------------------------------
st.subheader("Total anual de aquisições (todos os medicamentos)")

total_anual = (
    df_filtrado.groupby("Ano", as_index=False)["Quantidade"]
    .sum()
    .sort_values("Ano")
)

chart_total_anual = (
    alt.Chart(total_anual)
    .mark_bar()
    .encode(
        x=alt.X("Ano:O", title="Ano"),
        y=alt.Y("Quantidade:Q", title="Quantidade total adquirida", axis=alt.Axis(format=",.0f")),
        tooltip=[
            alt.Tooltip("Ano:O", title="Ano"),
            alt.Tooltip("Quantidade:Q", title="Total", format=",.0f")
        ],
    )
    .properties(height=400)
)

st.altair_chart(chart_total_anual, use_container_width=True)

# --------------------------------------------------------------------------------
# Gráfico 2: Composição por medicamento (barras empilhadas)
# --------------------------------------------------------------------------------
st.subheader("Composição das aquisições por medicamento (barras empilhadas)")

comp_anual_medicamento = (
    df_filtrado.groupby(["Ano", "medicamento"], as_index=False)["Quantidade"]
    .sum()
)

chart_stack = (
    alt.Chart(comp_anual_medicamento)
    .mark_bar()
    .encode(
        x=alt.X("Ano:O", title="Ano"),
        y=alt.Y("Quantidade:Q", title="Quantidade", axis=alt.Axis(format=",.0f")),
        color=alt.Color("medicamento:N", title="Medicamento"),
        tooltip=[
            alt.Tooltip("Ano:O", title="Ano"),
            alt.Tooltip("medicamento:N", title="Medicamento"),
            alt.Tooltip("Quantidade:Q", title="Quantidade", format=",.0f")
        ]
    )
    .properties(height=450)
)

st.altair_chart(chart_stack, use_container_width=True)

# --------------------------------------------------------------------------------
# Gráfico 3: Evolução por medicamento selecionado
# --------------------------------------------------------------------------------
st.subheader("Evolução anual por medicamento")

meds_disponiveis = sorted(df_filtrado["medicamento"].unique())

meds_selecionados = st.multiselect(
    "Selecione um ou mais medicamentos para comparar",
    options=meds_disponiveis,
    default=meds_disponiveis[:5] if len(meds_disponiveis) > 5 else meds_disponiveis
)

if meds_selecionados:
    df_meds = (
        df_filtrado[df_filtrado["medicamento"].isin(meds_selecionados)]
        .groupby(["Ano", "medicamento"], as_index=False)["Quantidade"]
        .sum()
    )

    chart_meds = (
        alt.Chart(df_meds)
        .mark_line(point=True)
        .encode(
            x=alt.X("Ano:O", title="Ano"),
            y=alt.Y("Quantidade:Q", title="Quantidade", axis=alt.Axis(format=",.0f")),
            color=alt.Color("medicamento:N", title="Medicamento"),
            tooltip=[
                alt.Tooltip("Ano:O", title="Ano"),
                alt.Tooltip("medicamento:N", title="Medicamento"),
                alt.Tooltip("Quantidade:Q", title="Quantidade", format=",.0f")
            ]
        )
        .properties(height=400)
    )

    st.altair_chart(chart_meds, use_container_width=True)
else:
    st.info("Selecione pelo menos um medicamento para visualizar a evolução.")

# --------------------------------------------------------------------------------
# Tabela de dados
# --------------------------------------------------------------------------------
with st.expander("Ver dados detalhados"):
    st.dataframe(df_filtrado.sort_values(["Ano", "medicamento"]), use_container_width=True)
