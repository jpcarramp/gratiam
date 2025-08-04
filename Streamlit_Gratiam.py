import streamlit as st
import pandas as pd
import plotly.express as px

# URL da planilha
sheet_url = "https://docs.google.com/spreadsheets/d/1XovoHw_Cot40MD-lxcmVyKaQUPlTcK1b3bNzIpxp1XM/edit?usp=sharing"
sheet_id = sheet_url.split("/")[5]
base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="

# Função para carregar uma aba da planilha
@st.cache_data
def carregar_dados(sheet_name):
    url = base_url + sheet_name
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

# Função para converter textos com formato brasileiro para float
def converter_valores(coluna):
    return (
        coluna.astype(str)
        .str.replace("\u00A0", "", regex=False)  # Remove espaços não quebráveis
        .str.replace(".", "", regex=False)       # Remove milhar
        .str.replace(",", ".", regex=False)      # Troca decimal
        .astype(float)
    )

# Configuração da página
st.set_page_config(page_title="Análise FIDC GRATIAM", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
    .stApp {
        background-color: #6495ED;
    }
    .metric-container {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
        text-align: center;
    }
    .metric-label {
        font-size: 18px;
        color: #333333;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

# Carregar os dados
df_aprop = carregar_dados("Apropriacao_Diaria_Estoque")
df_venc = carregar_dados("Vencimento_Diario_Estoque")

# Tratamento de datas
df_aprop['Dia_Analise'] = pd.to_datetime(df_aprop['Dia_Analise'], errors='coerce')
df_aprop['DATA'] = pd.to_datetime(df_aprop['DATA'], errors='coerce')
df_venc['Dia_Analise'] = pd.to_datetime(df_venc['Dia_Analise'], errors='coerce')
df_venc['DATA'] = pd.to_datetime(df_venc['DATA'], errors='coerce')

# Conversão de valores monetários para float
df_aprop['VALOR_APROPRIADO'] = converter_valores(df_aprop['VALOR_APROPRIADO'])
df_venc['VALOR_NOMINAL'] = converter_valores(df_venc['VALOR_NOMINAL'])

# Filtro lateral
datas_disponiveis = sorted(df_aprop['Dia_Analise'].dropna().unique())
data_analise = st.sidebar.date_input(
    "Selecione a data de análise:",
    value=datas_disponiveis[-1],
    min_value=datas_disponiveis[0],
    max_value=datas_disponiveis[-1]
)

# Título principal
st.title(f"Análise FIDC GRATIAM - Data da análise: {data_analise.strftime('%d/%m/%Y')}")

# Filtragem
dados_aprop = df_aprop[df_aprop['Dia_Analise'] == pd.to_datetime(data_analise)]
dados_venc = df_venc[df_venc['Dia_Analise'] == pd.to_datetime(data_analise)]

# Layout em colunas: gráfico e balão lado a lado
col1, col2 = st.columns([2, 1], gap="medium")

with col1:
    st.subheader("Valor Apropriado Diário")
    if not dados_aprop.empty:
        fig_aprop = px.line(
            dados_aprop,
            x='DATA',
            y='VALOR_APROPRIADO',
            title=None,
            labels={'VALOR_APROPRIADO': 'Valor (R$)', 'DATA': 'Data'},
            markers=True
        )
        fig_aprop.update_traces(
            line=dict(width=3),
            marker=dict(size=6),
            textposition="top center",
            texttemplate="%{y:.2s}"
        )
        fig_aprop.update_layout(
            yaxis_tickformat=",",
            plot_bgcolor="#f0f4ff",
            paper_bgcolor="#f0f4ff",
            xaxis=dict(
                title_font=dict(size=14, family="Arial", color="black"),
                tickfont=dict(size=12, family="Arial", color="black")
            ),
            yaxis=dict(
                title_font=dict(size=14, family="Arial", color="black"),
                tickfont=dict(size=12, family="Arial", color="black")
            ),
            margin=dict(l=40, r=40, t=20, b=40)
        )

        st.plotly_chart(fig_aprop, use_container_width=True)
    else:
        st.warning("Nenhum dado de apropriação encontrado para esta data.")

    st.subheader("Vencimentos por Data")
    if not dados_venc.empty:
        fig_venc = px.line(
            dados_venc,
            x='DATA',
            y='VALOR_NOMINAL',
            title=None,
            labels={'VALOR_NOMINAL': 'Valor (R$)', 'DATA': 'Data'},
            markers=True
        )
        fig_venc.update_traces(textposition="top center", texttemplate="%{y:.2s}")
        fig_venc.update_layout(yaxis_tickformat=",")
        st.plotly_chart(fig_venc, use_container_width=True)
    else:
        st.warning("Nenhum dado de vencimento encontrado para esta data.")

with col2:
    # Alinha o balão com o centro vertical dos gráficos
    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)

    total_aprop = dados_aprop['VALOR_APROPRIADO'].sum()
    valor_formatado = f"R$ {total_aprop:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Soma do Valor Apropriado no Período</div>
            <div class="metric-value">{valor_formatado}</div>
        </div>
    """, unsafe_allow_html=True)


with col1:
    st.subheader("Análise PDD")

    # Carrega e trata os dados
    df_pdd = carregar_dados("Pdd_Total_Previsto")
    df_pdd['Data'] = pd.to_datetime(df_pdd['Data'], dayfirst=True, errors='coerce')
    df_pdd['PDD Prevista'] = converter_valores(df_pdd['PDD Prevista'])

    df_pdd_agrupado = df_pdd.groupby('Data', as_index=False)['PDD Prevista'].sum()
    df_pdd_agrupado.rename(columns={'PDD Prevista': 'TOTAL PDD'}, inplace=True)
    df_pdd_agrupado = df_pdd_agrupado.sort_values("Data").reset_index(drop=True)

    # Calcular variação percentual
    df_pdd_agrupado['VARIAÇÃO'] = df_pdd_agrupado['TOTAL PDD'].pct_change() * 100

    # Armazenar coluna numérica para estilização condicional
    variacao_numerica = df_pdd_agrupado['VARIAÇÃO']

    # Formatação visual
    df_pdd_agrupado['TOTAL PDD'] = df_pdd_agrupado['TOTAL PDD'].map(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    df_pdd_agrupado['VARIAÇÃO'] = variacao_numerica.map(
        lambda x: f"{x:.2f}%" if pd.notnull(x) else "—"
    )

    # Estilização condicional com Styler
    def highlight_var(val):
        try:
            pct = float(val.replace('%','').replace(',','.'))
            if pct > 3:
                return 'background-color: #ffcccc'  # vermelho claro
        except:
            pass
        return ''

    styled_df = df_pdd_agrupado.style.applymap(highlight_var, subset=['VARIAÇÃO'])

    # Cria duas colunas: tabela e balão
    col_pdd_tabela, col_pdd_balao = st.columns([2, 1], gap="medium")

    with col_pdd_tabela:
        st.dataframe(styled_df, use_container_width=True)

    with col_pdd_balao:
        # Filtrar apenas datas futuras em relação à análise
        df_futuro = df_pdd_agrupado.copy()
        df_futuro['Data'] = pd.to_datetime(df_futuro['Data'], errors='coerce')
        df_futuro['VAR_NUM'] = variacao_numerica
        df_futuro = df_futuro[df_futuro['Data'] > pd.to_datetime(data_analise)]

        # Encontrar a data com a maior variação
        if not df_futuro.empty and df_futuro['VAR_NUM'].notnull().any():
            max_var_row = df_futuro.loc[df_futuro['VAR_NUM'].idxmax()]
            data_critica = max_var_row['Data'].strftime("%d/%m")
            variacao_critica = max_var_row['VAR_NUM']
            variacao_formatada = f"{variacao_critica:.2f}".replace(".", ",") + "%"

            st.markdown(f"""
                <div class="metric-container" style="margin-top: 20px;">
                    <div class="metric-label">O dia mais crítico para o fundo será o dia</div>
                    <div class="metric-value">{data_critica}, com variação de {variacao_formatada}</div>
                </div>
            """, unsafe_allow_html=True)



