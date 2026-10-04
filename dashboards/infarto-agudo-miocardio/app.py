from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Infarto Agudo do Miocárdio",
    page_icon="❤️",
    layout="wide",
)

REQUIRED = [
    "ano",
    "uf",
    "municipio",
    "sexo",
    "faixa_etaria",
    "internacoes",
    "obitos_hospitalares",
]

ALIASES = {
    "year": "ano",
    "estado": "uf",
    "state": "uf",
    "cidade": "municipio",
    "município": "municipio",
    "internação": "internacoes",
    "internações": "internacoes",
    "hospitalizacoes": "internacoes",
    "hospitalizações": "internacoes",
    "obitos": "obitos_hospitalares",
    "óbitos": "obitos_hospitalares",
    "mortes_hospitalares": "obitos_hospitalares",
    "faixa etária": "faixa_etaria",
    "faixa etaria": "faixa_etaria",
}


def demo_data() -> pd.DataFrame:
    """Valores artificiais para demonstrar o funcionamento do painel."""
    locations = [
        ("RO", "Porto Velho", 1.00),
        ("RO", "Jaru", 0.28),
        ("RO", "Ji-Paraná", 0.44),
        ("RO", "Ariquemes", 0.38),
        ("RO", "Cacoal", 0.34),
    ]
    age_groups = [("40–59 anos", 0.34), ("60–79 anos", 0.48), ("80 anos ou mais", 0.18)]
    sexes = [("Feminino", 0.44), ("Masculino", 0.56)]
    rows = []

    for year_index, year in enumerate(range(2019, 2025)):
        trend = 1 + year_index * 0.045
        for uf, city, location_weight in locations:
            for age, age_weight in age_groups:
                for sex, sex_weight in sexes:
                    admissions = round(
                        62 * location_weight * trend * age_weight * sex_weight
                    )
                    deaths = round(admissions * (0.09 + 0.015 * age_weight))
                    rows.append(
                        {
                            "ano": year,
                            "uf": uf,
                            "municipio": city,
                            "sexo": sex,
                            "faixa_etaria": age,
                            "internacoes": admissions,
                            "obitos_hospitalares": deaths,
                        }
                    )
    return pd.DataFrame(rows)


def load_csv(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.getvalue()
    try:
        frame = pd.read_csv(io.BytesIO(raw), sep=None, engine="python")
    except UnicodeDecodeError:
        frame = pd.read_csv(
            io.BytesIO(raw), sep=None, engine="python", encoding="latin-1"
        )

    frame.columns = [str(name).strip().lower() for name in frame.columns]
    frame = frame.rename(columns=ALIASES)
    missing = [name for name in REQUIRED if name not in frame.columns]
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(missing)
            + ". Baixe o modelo CSV na barra lateral."
        )

    frame = frame[REQUIRED].copy()
    for column in ["ano", "internacoes", "obitos_hospitalares"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(
        subset=["ano", "internacoes", "obitos_hospitalares"]
    )
    if frame.empty:
        raise ValueError("O arquivo não contém linhas válidas.")

    for column in ["ano", "internacoes", "obitos_hospitalares"]:
        if ((frame[column] % 1) != 0).any():
            raise ValueError(f"A coluna {column} deve conter números inteiros.")
        frame[column] = frame[column].astype(int)

    for column in ["uf", "municipio", "sexo", "faixa_etaria"]:
        frame[column] = (
            frame[column].fillna("Não informado").astype(str).str.strip()
        )

    if (frame[["internacoes", "obitos_hospitalares"]] < 0).any().any():
        raise ValueError("Internações e óbitos não podem ser negativos.")
    if (frame["obitos_hospitalares"] > frame["internacoes"]).any():
        raise ValueError(
            "Há linhas com mais óbitos hospitalares do que internações. "
            "Revise a planilha."
        )
    return frame


st.title("Infarto Agudo do Miocárdio")
st.caption("Painel exploratório de internações e óbitos hospitalares agregados")

st.warning(
    "A demonstração contém somente valores fictícios para visualizar o painel. "
    "Não são dados reais do SUS e não devem ser usados em análises ou trabalhos."
)

with st.sidebar:
    st.header("Fonte dos dados")
    mode = st.radio(
        "Escolha uma opção",
        ["Demonstração fictícia", "Enviar CSV agregado"],
    )
    uploaded = None
    source_note = "Demonstração fictícia — valores simulados"

    if mode == "Enviar CSV agregado":
        uploaded = st.file_uploader("Selecione um arquivo CSV", type=["csv"])
        source_note = st.text_input(
            "Fonte e observação",
            value="DATASUS / TabNet — informe a base e os filtros usados",
        )

    template = pd.DataFrame(columns=REQUIRED).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar modelo CSV",
        template,
        file_name="modelo_infarto.csv",
        mime="text/csv",
    )
    st.divider()
    st.caption(
        "Use dados agregados. Não envie nomes, CPF, prontuários ou identificadores "
        "de pacientes."
    )

if mode == "Demonstração fictícia":
    data = demo_data()
else:
    if uploaded is None:
        st.info("Envie um CSV agregado para começar.")
        st.write("Colunas esperadas:", ", ".join(REQUIRED))
        st.stop()
    try:
        data = load_csv(uploaded)
    except Exception as error:
        st.error(str(error))
        st.stop()

with st.sidebar:
    st.header("Filtros")
    years = sorted(data["ano"].unique())
    if len(years) == 1:
        year_range = (years[0], years[0])
        st.write(f"Ano: {years[0]}")
    else:
        year_range = st.select_slider(
            "Período",
            options=years,
            value=(years[0], years[-1]),
        )

    states = sorted(data["uf"].unique())
    selected_states = st.multiselect("UF", states, default=states)
    available_cities = sorted(
        data.loc[data["uf"].isin(selected_states), "municipio"].unique()
    )
    selected_cities = st.multiselect(
        "Município", available_cities, default=available_cities
    )
    sexes = sorted(data["sexo"].unique())
    selected_sexes = st.multiselect("Sexo", sexes, default=sexes)
    ages = sorted(data["faixa_etaria"].unique())
    selected_ages = st.multiselect("Faixa etária", ages, default=ages)

filtered = data[
    data["ano"].between(year_range[0], year_range[1])
    & data["uf"].isin(selected_states)
    & data["municipio"].isin(selected_cities)
    & data["sexo"].isin(selected_sexes)
    & data["faixa_etaria"].isin(selected_ages)
].copy()

st.caption(f"Fonte informada: {source_note}")
if filtered.empty:
    st.info("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

admissions = int(filtered["internacoes"].sum())
hospital_deaths = int(filtered["obitos_hospitalares"].sum())
hospital_percent = hospital_deaths / admissions * 100 if admissions else 0

st.caption(
    f"Período: {year_range[0]}–{year_range[1]} · "
    f"Registros agregados: {len(filtered):,}"
)
k1, k2, k3 = st.columns(3)
k1.metric("Internações registradas", f"{admissions:,}")
k2.metric("Óbitos hospitalares no SIH", f"{hospital_deaths:,}")
k3.metric("Óbitos hospitalares / internações", f"{hospital_percent:.1f}%")
st.caption(
    "O percentual usa internações e óbitos hospitalares do mesmo arquivo filtrado. "
    "Não representa mortalidade geral da população."
)

st.subheader("Evolução anual")
annual = (
    filtered.groupby("ano", as_index=False)[
        ["internacoes", "obitos_hospitalares"]
    ]
    .sum()
    .sort_values("ano")
)
left, right = st.columns(2)
with left:
    chart = px.line(
        annual,
        x="ano",
        y="internacoes",
        markers=True,
        title="Internações",
        labels={"ano": "Ano", "internacoes": "Internações"},
    )
    st.plotly_chart(chart, use_container_width=True)
with right:
    chart = px.line(
        annual,
        x="ano",
        y="obitos_hospitalares",
        markers=True,
        title="Óbitos hospitalares",
        labels={"ano": "Ano", "obitos_hospitalares": "Óbitos"},
    )
    st.plotly_chart(chart, use_container_width=True)

st.subheader("Distribuição por local e faixa etária")
left, right = st.columns(2)
with left:
    by_city = (
        filtered.groupby(["municipio", "uf"], as_index=False)["internacoes"]
        .sum()
        .sort_values("internacoes", ascending=False)
        .head(12)
    )
    by_city["local"] = by_city["municipio"] + " (" + by_city["uf"] + ")"
    chart = px.bar(
        by_city.sort_values("internacoes"),
        x="internacoes",
        y="local",
        orientation="h",
        title="Internações por município",
        labels={"internacoes": "Internações", "local": ""},
    )
    st.plotly_chart(chart, use_container_width=True)
with right:
    by_age = (
        filtered.groupby("faixa_etaria", as_index=False)["internacoes"]
        .sum()
        .sort_values("internacoes", ascending=False)
    )
    chart = px.bar(
        by_age,
        x="faixa_etaria",
        y="internacoes",
        title="Internações por faixa etária",
        labels={"faixa_etaria": "Faixa etária", "internacoes": "Internações"},
    )
    st.plotly_chart(chart, use_container_width=True)

st.subheader("Tabela filtrada")
st.dataframe(
    filtered.sort_values(["ano", "uf", "municipio"]),
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    "Baixar dados filtrados",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="infarto_dados_filtrados.csv",
    mime="text/csv",
)

with st.expander("Fontes, definições e limitações"):
    st.markdown(
        """
- Este protótipo não faz diagnóstico nem recomenda tratamento.
- O SIH/SUS descreve internações registradas no sistema; não representa, sozinho,
  todas as internações da rede privada nem todas as pessoas com infarto.
- Óbitos hospitalares do SIH e óbitos por causa básica do SIM são medidas distintas.
  Mantenha cada fonte separada e informe os filtros usados.
- Não calcule taxas populacionais sem denominadores populacionais compatíveis.
- Antes de divulgar resultados, confira CID-10, período, local de residência ou
  internação e a versão da base consultada.
        """
    )
