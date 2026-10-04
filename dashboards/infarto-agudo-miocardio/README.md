# Painel de Infarto Agudo do Miocárdio

Protótipo educacional para explorar contagens agregadas de internações e óbitos relacionados ao infarto. A aplicação não é ferramenta clínica.

## Executar localmente

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

No Windows, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

## O que o painel oferece

- Filtros reativos por ano, UF, município, sexo e faixa etária.
- Indicadores, tendências anuais e comparações interativas com Plotly.
- Resumo descritivo calculado a partir do recorte filtrado.
- Aba própria para SIH/SUS e outra para SIM, sem combinar seus numeradores.
- Download das tabelas filtradas e modelos CSV.
- Aba com fontes, definições e limitações.

## Usar os dados de demonstração

A opção **Demonstração fictícia** gera contagens artificiais de Rondônia para mostrar os filtros e gráficos. Os valores não são estatísticas oficiais e não devem ser citados.

## Importar dados agregados

Selecione **Enviar arquivos CSV**. O arquivo do SIH/SUS é necessário; o do SIM é opcional e permanece separado. Os dois modelos CSV podem ser baixados na barra lateral.

### Modelo SIH/SUS

Colunas: `ano, uf, municipio, sexo, faixa_etaria, internacoes, obitos_hospitalares`

Use a contagem de internações e de óbitos hospitalares do mesmo recorte. O percentual mostrado é calculado como óbitos hospitalares divididos por internações; ele não representa mortalidade geral da população.

### Modelo SIM

Colunas: `ano, uf, municipio, sexo, faixa_etaria, obitos_sim`

Use a contagem de óbitos por causa básica segundo a consulta do SIM. O painel apresenta essa série separadamente; não divide óbitos do SIM pelas internações do SIH.

Carregue somente dados agregados. Não envie microdados com nomes, CPF, prontuários ou identificadores pessoais.

## Fontes oficiais

- [Morbidade Hospitalar do SUS (SIH/SUS) — DATASUS](https://datasus.saude.gov.br/acesso-a-informacao/morbidade-hospitalar-do-sus-sih-sus/)
- [Mortalidade desde 1996 pela CID-10 — DATASUS](https://datasus.saude.gov.br/mortalidade-desde-1996-pela-cid-10/)
- [Informações de Saúde (TabNet) — DATASUS](https://datasus.saude.gov.br/informacoes-de-saude-tabnet/)

Registre no campo de fonte qual CID-10, período, tipo de localidade (residência ou ocorrência/internação) e versão da consulta foram usados. Comece com CID-10 I21 e documente qualquer ampliação do recorte. O SIH/SUS não representa, por si só, todas as internações da rede privada.

## Referências de design

O protótipo combina padrões de projetos conhecidos sem copiar código: Streamlit para interação simples em Python; Plotly Dash para exploração reativa de gráficos; Superset e Metabase para filtros, indicadores e separação clara das métricas; Evidence para exibir leitura e metodologia junto aos dados.

A consulta de dados por linguagem natural inspirada no Vanna fica para uma etapa posterior: primeiro é necessário validar as bases, limitar as perguntas a dados agregados e decidir como configurar um provedor de IA com segurança. O repositório Vanna consultado está arquivado, então não é dependência deste protótipo.

## Próximas melhorias

1. Validar arquivos oficiais agregados do SIH/SUS e do SIM para Rondônia/Jaru.
2. Documentar denominadores e método antes de incluir taxas populacionais.
3. Acrescentar uma camada opcional de perguntas em linguagem natural somente após validação e configuração segura.
