# Painel de Infarto Agudo do Miocárdio

Protótipo educacional para explorar internações e óbitos hospitalares agregados relacionados ao infarto agudo do miocárdio. A aplicação não é ferramenta clínica.

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

## Testar o painel

A opção **Demonstração fictícia** abre um conjunto gerado no código, apenas para mostrar os gráficos e filtros. Os números não são estatísticas oficiais nem devem ser citados.

Para usar dados reais, selecione **Enviar CSV agregado** e carregue um arquivo com estas colunas:

| Coluna | Conteúdo |
|---|---|
| ano | Ano de referência |
| uf | Sigla do estado |
| municipio | Município |
| sexo | Categoria de sexo disponível na base |
| faixa_etaria | Grupo etário |
| internacoes | Contagem de internações |
| obitos_hospitalares | Óbitos hospitalares registrados no mesmo recorte de internações |

O próprio painel permite baixar um CSV vazio com os nomes esperados. Use somente dados agregados; não carregue microdados com identificadores pessoais.

## Fontes oficiais para preparar a primeira base

- [Morbidade Hospitalar do SUS (SIH/SUS) — DATASUS](https://datasus.saude.gov.br/acesso-a-informacao/morbidade-hospitalar-do-sus-sih-sus/)
- [Mortalidade desde 1996 pela CID-10 — DATASUS](https://datasus.saude.gov.br/mortalidade-desde-1996-pela-cid-10/)
- [Informações de Saúde (TabNet) — DATASUS](https://datasus.saude.gov.br/informacoes-de-saude-tabnet/)

Comece com CID-10 I21 e documente os códigos selecionados, o período e se o local representa residência ou ocorrência/internação. Mantenha SIH/SUS e SIM como fontes separadas no arquivo e na interpretação: óbitos hospitalares do SIH não equivalem a todos os óbitos por infarto do SIM. O SIH/SUS não representa todas as internações da rede privada.

## Indicadores exibidos

- Total de internações no recorte selecionado.
- Óbitos hospitalares registrados no arquivo agregado.
- Percentual calculado como óbitos hospitalares ÷ internações × 100, somente dentro do mesmo arquivo SIH e dos mesmos filtros.
- Tendência anual e distribuição de internações por município e faixa etária.

A versão inicial não calcula taxas por 100 mil habitantes. Isso exigiria denominadores populacionais compatíveis por ano e local, com metodologia documentada.

## Próximas melhorias

1. Preparar e validar uma extração real do SIH/SUS para Rondônia e Jaru.
2. Acrescentar uma seção separada para óbitos do SIM.
3. Incluir população e taxas após validar os denominadores.
4. Publicar uma demonstração com aviso visível sobre as fontes e limitações.
