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

COMMON_COLUMNS = ["ano", "uf", "municipio", "sexo", "faixa_etaria"]
SIH_COLUMNS = COMMON_COLUMNS + ["internacoes", "obitos_hospitalares"]
SIM_COLUMNS = COMMON_COLUMNS + ["obitos_sim"]

ALIASES = {
    "year": "ano",
    "estado": "uf",
    "state": "uf",
    "cidade": "municipio",
    "município": "municipio",
    "faixa etaria": "faixa_etaria",
    "faixa etária": "faixa_etaria",
    "internacao": "internacoes",
    "internação": "internacoes",
    "internacoes": "internacoes",
    "internações": "internacoes",
    "hospitalizacoes": "internacoes",
    "hospitalizações": "internacoes",
    "obitos": "obitos_hospitalares",
    "óbitos": "obitos_hospitalares",
    "mortes_hospitalares": "obitos_hospitalares",
    "óbitos hospitalares": "obitos_hospitalares",
    "obitos_sim": "obitos_sim",
    "óbitos sim": "obitos_sim",
    "obitos por infarto": "obitos_sim",
}


def make_demo_sih() -> pd.DataFrame:
    """Valores artificiais; servem somente para visualizar as funções do painel."""
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
        for uf, city, place_weight in locations:
            for age, age_weight in age_groups:
                for sex, sex_weight in sexes:
                    admissions = round(62 * place_weight * trend * age_weight * sex_weight)
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


def make_demo_sim() -> pd.DataFrame:
    """Série fictícia independente para demonstrar a aba do SIM."""
    locations = [
        ("RO", "Porto Velho", 1.00),
        ("RO", "Jaru", 0.28),
        ("RO", "Ji-Paraná", 0.44),
        ("RO", "Ariquemes", 0.38),
        ("RO", "Cacoal", 0.34),
    ]
    age_groups = [("40–59 anos", 0.30), ("60–79 anos", 0.48), ("80 anos ou mais", 0.22)]
    sexes = [("Feminino", 0.44), ("Masculino", 0.56)]
    rows = []
    for year_index, year in enumerate(range(2019, 2025)):
        for uf, city, place_weight in locations:
            for age, age_weight in age_groups:
                for sex, sex_weight in sexes:
                    deaths = round(11 * place_weight * age_weight * sex_weight * (1 + year_index * 0.035))
                    rows.append(
                        {
                            "ano": year,
                            "uf": uf,
                            "municipio": city,
                            "sexo": sex,
                            "faixa_etaria": age,
                            "obitos_sim": deaths,
                        }
                    )
    return pd.DataFrame(rows)


def load_aggregated_csv(uploaded_file, dataset: str) -> pd.DataFrame:
    required = SIH_COLUMNS if dataset == "SIH/SUS" else SIM_COLUMNS
    raw = uploaded_file.getvalue()
    try:
        frame = pd.read_csv(io.BytesIO(raw), sep=None, engine="python")
    except UnicodeDecodeError:
        frame = pd.read_csv(
            io.BytesIO(raw), sep=None, engine="python", encoding="latin-1"
        )

    frame.columns = [str(name).strip().lower() for name in frame.columns]
    frame = frame.rename(columns=ALIASES)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(
            f"Arquivo {dataset}: faltam as colunas "
            + ", ".join(missing)
            + ". Baixe o modelo CSV correspondente na barra lateral."
        )

    frame = frame[required].copy()
    count_columns = ["internacoes", "obitos_hospitalares"] if dataset == "SIH/SUS" else ["obitos_sim"]
    for column in ["ano"] + count_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["ano"] + count_columns)
    if frame.empty:
        raise ValueError(f"Arquivo {dataset}: não há linhas válidas.")

    for column in ["ano"] + count_columns:
        if ((frame[column] % 1) != 0).any():
            raise ValueError(f"Arquivo {dataset}: a coluna {column} deve conter inteiros.")
        frame[column] = frame[column].astype(int)

    for column in COMMON_COLUMNS[1:]:
        frame[column] = frame[column].fillna("Não informado").astype(str).str.strip()

    if (frame[count_columns] < 0).any().any():
        raise ValueError(f"Arquivo {dataset}: contagens não podem ser negativas.")
    if dataset == "SIH/SUS" and (
        frame["obitos_hospitalares"] > frame["internacoes"]
    ).any():
        raise ValueError(
            "No SIH/SUS, há linhas com óbitos hospitalares acima das internações. "
            "Revise o arquivo."
        )
    return frame


def filter_data(frame: pd.DataFrame, years, states, cities, sexes, ages):
    return frame[
        frame["ano"].isin(years)
        & frame["uf"].isin(states)
        & frame["municipio"].isin(cities)
        & frame["sexo"].isin(sexes)
        & frame["faixa_etaria"].isin(ages)
    ].copy()


def describe_sih(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "Nenhum registro corresponde aos filtros selecionados."
    annual = frame.groupby("ano")["internacoes"].sum().sort_index()
    total = int(annual.sum())
    highest_city = (
        frame.groupby("municipio")["internacoes"].sum().sort_values(ascending=False)
    )
    if len(annual) > 1:
        first_year, last_year = int(annual.index[0]), int(annual.index[-1])
        first_value, last_value = int(annual.iloc[0]), int(annual.iloc[-1])
        if first_value:
            change = (last_value / first_value - 1) * 100
            trend = (
                f"Entre {first_year} e {last_year}, as internações passaram de "
                f"{first_value:,} para {last_value:,} ({change:+.1f}%)."
            )
        else:
            trend = f"Há dados para {len(annual)} anos no período selecionado."
    else:
        trend = "Selecione mais de um ano para comparar a tendência."
    city_text = (
        f"Maior contagem no recorte: {highest_city.index[0]} "
        f"({int(highest_city.iloc[0]):,} internações)."
        if not highest_city.empty
        else ""
    )
    return f"{trend} Total no recorte: {total:,}. {city_text}"


st.title("Infarto Agudo do Miocárdio")
st.caption("Painel exploratório de internações e mortalidade agregadas")

st.info(
    "Demonstração fictícia: os números de exemplo são simulados, não representam "
    "dados oficiais e não devem ser citados."
)

with st.sidebar:
    st.header("Dados")
    data_mode = st.radio(
        "Origem",
        ["Demonstração fictícia", "Enviar arquivos CSV"],
    )
    sih_file = sim_file = None
    sih_source = "Demonstração fictícia — valores simulados"
    sim_source = "Demonstração fictícia — valores simulados"

    if data_mode == "Enviar arquivos CSV":
        sih_file = st.file_uploader("SIH/SUS — internações agregadas", type=["csv"])
        sim_file = st.file_uploader("SIM — óbitos agregados (opcional)", type=["csv"])
        sih_source = st.text_input(
            "Fonte SIH e recorte",
            value="DATASUS/TabNet — informe CID, período e local consultado",
        )
        if sim_file:
            sim_source = st.text_input(
                "Fonte SIM e recorte",
                value="DATASUS/TabNet — informe causa, período e local consultado",
            )
        st.download_button(
            "Modelo CSV SIH/SUS",
            pd.DataFrame(columns=SIH_COLUMNS).to_csv(index=False).encode("utf-8"),
            file_name="modelo_sih_infarto.csv",
            mime="text/csv",
        )
        st.download_button(
            "Modelo CSV SIM",
            pd.DataFrame(columns=SIM_COLUMNS).to_csv(index=False).encode("utf-8"),
            file_name="modelo_sim_infarto.csv",
            mime="text/csv",
        )
    st.divider()
    st.caption(
        "Envie apenas dados agregados. Não carregue nomes, CPF, prontuários ou "
        "identificadores de pacientes."
    )

if data_mode == "Demonstração fictícia":
    sih = make_demo_sih()
    sim = make_demo_sim()
else:
    if sih_file is None:
        st.warning("Envie um CSV agregado do SIH/SUS para abrir o painel.")
        st.stop()
    try:
        sih = load_aggregated_csv(sih_file, "SIH/SUS")
        sim = load_aggregated_csv(sim_file, "SIM") if sim_file else None
    except Exception as error:
        st.error(str(error))
        st.stop()

with st.sidebar:
    st.header("Filtros")
    years_available = sorted(sih["ano"].unique())
    selected_years = st.multiselect(
        "Ano",
        years_available,
        default=years_available,
    )
    states_available = sorted(sih["uf"].unique())
    selected_states = st.multiselect(
        "UF",
        states_available,
        default=states_available,
    )
    cities_available = sorted(
        sih.loc[sih["uf"].isin(selected_states), "municipio"].unique()
    )
    selected_cities = st.multiselect(
        "Município",
        cities_available,
        default=cities_available,
    )
    sexes_available = sorted(sih["sexo"].unique())
    selected_sexes = st.multiselect(
        "Sexo",
        sexes_available,
        default=sexes_available,
    )
    ages_available = sorted(sih["faixa_etaria"].unique())
    selected_ages = st.multiselect(
        "Faixa etária",
        ages_available,
        default=ages_available,
    )

selected_sih = filter_data(
    sih, selected_years, selected_states, selected_cities, selected_sexes, selected_ages
)
selected_sim = (
    filter_data(sim, selected_years, selected_states, selected_cities, selected_sexes, selected_ages)
    if sim is not None
    else None
)

tab_overview, tab_mortality, tab_method = st.tabs(
    ["Visão geral — SIH/SUS", "Mortalidade — SIM", "Dados e metodologia"]
)

with tab_overview:
    st.subheader("Internações e óbitos hospitalares")
    st.caption(f"Fonte declarada: {sih_source}")
    if selected_sih.empty:
        st.info("Nenhum registro do SIH/SUS corresponde aos filtros.")
    else:
        admissions_total = int(selected_sih["internacoes"].sum())
        hospital_deaths_total = int(selected_sih["obitos_hospitalares"].sum())
        hospital_share = (
            hospital_deaths_total / admissions_total * 100 if admissions_total else 0
        )
        k1, k2, k3 = st.columns(3)
        k1.metric("Internações registradas", f"{admissions_total:,}")
        k2.metric("Óbitos hospitalares", f"{hospital_deaths_total:,}")
        k3.metric("Óbitos hospitalares / internações", f"{hospital_share:.1f}%")
        st.caption(
            "Esse percentual usa apenas contagens do SIH/SUS no mesmo recorte; "
            "não é mortalidade geral da população."
        )

        st.markdown("#### Leitura automática do recorte")
        st.write(describe_sih(selected_sih))

        annual = (
            selected_sih.groupby("ano", as_index=False)[
                ["internacoes", "obitos_hospitalares"]
            ]
            .sum()
            .sort_values("ano")
        )
        left, right = st.columns(2)
        with left:
            fig = px.line(
                annual,
                x="ano",
                y="internacoes",
                markers=True,
                title="Internações por ano",
                labels={"ano": "Ano", "internacoes": "Internações"},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=45, b=10), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.line(
                annual,
                x="ano",
                y="obitos_hospitalares",
                markers=True,
                title="Óbitos hospitalares por ano",
                labels={"ano": "Ano", "obitos_hospitalares": "Óbitos"},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=45, b=10), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        left, right = st.columns(2)
        with left:
            by_city = (
                selected_sih.groupby(["municipio", "uf"], as_index=False)["internacoes"]
                .sum()
                .sort_values("internacoes", ascending=False)
                .head(12)
            )
            by_city["local"] = by_city["municipio"] + " (" + by_city["uf"] + ")"
            fig = px.bar(
                by_city.sort_values("internacoes"),
                x="internacoes",
                y="local",
                orientation="h",
                title="Internações por município",
                labels={"internacoes": "Internações", "local": ""},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=45, b=10))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            by_age = (
                selected_sih.groupby("faixa_etaria", as_index=False)["internacoes"]
                .sum()
                .sort_values("internacoes", ascending=False)
            )
            fig = px.bar(
                by_age,
                x="faixa_etaria",
                y="internacoes",
                title="Internações por faixa etária",
                labels={"faixa_etaria": "Faixa etária", "internacoes": "Internações"},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=45, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver tabela agregada SIH/SUS"):
            st.dataframe(
                selected_sih.sort_values(["ano", "uf", "municipio"]),
                use_container_width=True,
                hide_index=True,
            )
        st.download_button(
            "Baixar recorte SIH/SUS",
            selected_sih.to_csv(index=False).encode("utf-8"),
            file_name="sih_infarto_filtrado.csv",
            mime="text/csv",
        )

with tab_mortality:
    st.subheader("Óbitos por causa básica — SIM")
    if selected_sim is None:
        st.info(
            "Envie também um CSV agregado do SIM para explorar óbitos por causa básica. "
            "Essa fonte fica separada do SIH/SUS."
        )
    elif selected_sim.empty:
        st.info("Nenhum registro do SIM corresponde aos filtros.")
    else:
        st.caption(f"Fonte declarada: {sim_source}")
        deaths_total = int(selected_sim["obitos_sim"].sum())
        st.metric("Óbitos registrados no SIM", f"{deaths_total:,}")
        annual_sim = (
            selected_sim.groupby("ano", as_index=False)["obitos_sim"]
            .sum()
            .sort_values("ano")
        )
        fig = px.line(
            annual_sim,
            x="ano",
            y="obitos_sim",
            markers=True,
            title="Óbitos por ano — SIM",
            labels={"ano": "Ano", "obitos_sim": "Óbitos"},
        )
        fig.update_layout(margin=dict(l=10, r=10, t=45, b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver tabela agregada SIM"):
            st.dataframe(
                selected_sim.sort_values(["ano", "uf", "municipio"]),
                use_container_width=True,
                hide_index=True,
            )
        st.download_button(
            "Baixar recorte SIM",
            selected_sim.to_csv(index=False).encode("utf-8"),
            file_name="sim_infarto_filtrado.csv",
            mime="text/csv",
        )
        st.warning(
            "Não divida os óbitos do SIM pelas internações do SIH/SUS para calcular "
            "letalidade hospitalar: são bases e universos diferentes."
        )

with tab_method:
    st.subheader("Definições e limites")
    st.markdown(
        """
- O protótipo foi pensado para consultas agregadas sobre infarto agudo do miocárdio.
  Documente os códigos CID-10 selecionados na extração e mantenha o mesmo recorte
  temporal e geográfico em cada análise.
- SIH/SUS: internações e óbitos hospitalares informados na base de internações.
  A cobertura não equivale a todas as internações da rede privada.
- SIM: óbitos registrados por causa básica. A contagem é mostrada separadamente.
- O painel não calcula taxa populacional. Para isso, são necessários denominadores
  populacionais compatíveis por ano e local.
- Os dados de demonstração são gerados artificialmente e não são estatísticas reais.
- Não é uma ferramenta diagnóstica ou de decisão clínica.
        """
    )
    st.markdown(
        "[Morbidade Hospitalar do SUS (SIH/SUS) — DATASUS](https://datasus.saude.gov.br/acesso-a-informacao/morbidade-hospitalar-do-sus-sih-sus/)"
        + chr(10)
        + "[Mortalidade por CID-10 — DATASUS](https://datasus.saude.gov.br/mortalidade-desde-1996-pela-cid-10/)"
        + chr(10)
        + "[Informações de Saúde (TabNet) — DATASUS](https://datasus.saude.gov.br/informacoes-de-saude-tabnet/)"
    )
