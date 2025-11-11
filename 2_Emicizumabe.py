# arquivo: pagina_emicizumabe_limpo.py
# executar: streamlit run pagina_emicizumabe_limpo.py

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Emicizumabe – Cenários Hemobrás e Roche", layout="wide")
st.title("Emicizumabe – Cenários Hemobrás e Roche")

# ------------------------ utilitário para ler CSV ------------------------ #
@st.cache_data(show_spinner=False)
def load_csv_auto(path: str) -> pd.DataFrame:
    for sep in (";", ",", None):
        try:
            if sep is None:
                return pd.read_csv(path, sep=None, engine="python", dtype=str)
            return pd.read_csv(path, sep=sep, dtype=str)
        except Exception:
            continue
    raise RuntimeError(f"Falha ao ler CSV: {path}")

# ---------------------------- leitura dos dados -------------------------- #
PATH_HB = "dados_emicizumabe_HB.csv"
PATH_ROCHE = "dados_emicizumabe_ROCHE.csv"

try:
    df_hb = load_csv_auto(PATH_HB)
    df_roche = load_csv_auto(PATH_ROCHE)
except Exception as e:
    st.error(f"Erro ao carregar CSVs: {e}")
    st.stop()

# ------------------------------ exibição pura ----------------------------- #
tab_hb, tab_roche = st.tabs(["Dados Hemobrás", "Dados ROCHE"])

with tab_hb:
    st.subheader("Cenário Hemobrás (Hemo 8R – UI)", divider="gray")
    st.data_editor(
        df_hb,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",   # impede adicionar novas linhas
        disabled=True,      # bloqueia edição
    )

with tab_roche:
    st.subheader("Cenário ROCHE (Emicizumabe – mg)", divider="gray")
    st.data_editor(
        df_roche,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=True,
    )

st.caption("Visualização somente leitura das tabelas originais. Nenhum dado é alterado.")
