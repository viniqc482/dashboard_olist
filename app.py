import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Dashboard Olist", layout="wide")

st.title("📊 Dashboard E-commerce - Olist")

# -----------------------------
# DADOS (PARQUET)
# -----------------------------
df = pd.read_parquet("receita.parquet")
df_pedidos = pd.read_parquet("pedidos.parquet")
df_ticket = pd.read_parquet("ticket.parquet")
df_entrega = pd.read_parquet("entrega.parquet")
df_reviews = pd.read_parquet("reviews.parquet")
df_geo = pd.read_parquet("geo.parquet")
df_vendedores = pd.read_parquet("vendedores.parquet")
df_produtos = pd.read_parquet("produtos.parquet")

# -----------------------------
# 🔥 BASE ÚNICA (FATO)
# -----------------------------
df_fato = pd.read_parquet("fato.parquet")
df_fato['mes'] = pd.to_datetime(df_fato['mes'])
# tratamento
for d in [df, df_pedidos, df_ticket]:
    d['mes'] = pd.to_datetime(d['mes'])
    d.sort_values('mes', inplace=True)

# -----------------------------
# 🎨 ESTILO SIDEBAR (BONITO)
# -----------------------------
st.sidebar.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
    .filtro-titulo {
        font-size:18px;
        font-weight:600;
        margin-bottom:10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown('<p class="filtro-titulo">🔎 Filtros</p>', unsafe_allow_html=True)

# -----------------------------
# VARIÁVEIS BASE
# -----------------------------
data_min = df['mes'].min().date()
data_max = df['mes'].max().date()

# inicialização
if "reset" not in st.session_state:
    st.session_state.reset = False

# -----------------------------
# BOTÃO LIMPAR
# -----------------------------
if st.sidebar.button("🔄 Limpar filtros"):
    st.session_state["data_range"] = (data_min, data_max)
    st.session_state["estado"] = "Todos"
    st.session_state["cidade"] = "Todas"
    st.session_state["categoria"] = "Todas"
    st.session_state.reset = not st.session_state.reset
    st.rerun()

# -----------------------------
# DATA
# -----------------------------
data_range = st.sidebar.date_input(
    "📅 Período",
    value=st.session_state.get("data_range", (data_min, data_max)),
    min_value=data_min,
    max_value=data_max,
    key=f"data_{st.session_state.reset}"
)

# -----------------------------
# ESTADO
# -----------------------------
estados = sorted(df_geo['estado'].unique())

estado = st.sidebar.selectbox(
    "📍 Estado",
    ["Todos"] + estados,
    index=(["Todos"] + estados).index(st.session_state.get("estado", "Todos")),
    key=f"estado_{st.session_state.reset}"
)

# -----------------------------
# CIDADE
# -----------------------------
if estado != "Todos":
    cidades = sorted(df_geo[df_geo['estado'] == estado]['cidade'].unique())
else:
    cidades = sorted(df_geo['cidade'].unique())

cidade = st.sidebar.selectbox(
    "🏙️ Cidade",
    ["Todas"] + cidades,
    index=0,
    key=f"cidade_{st.session_state.reset}"
)

# -----------------------------
# 🛒 CATEGORIA (NOVO)
# -----------------------------
categorias = sorted(df_produtos['categoria'].dropna().unique())

categoria = st.sidebar.selectbox(
    "🛒 Categoria",
    ["Todas"] + categorias,
    index=(["Todas"] + categorias).index(st.session_state.get("categoria", "Todas"))
    if st.session_state.get("categoria", "Todas") in categorias else 0,
    key=f"categoria_{st.session_state.reset}"
)

# -----------------------------
# FILTRO VENDEDORES (NOVO)
# -----------------------------
df_vendedores_filtrado = df_vendedores.copy()

if estado != "Todos" and 'estado' in df_vendedores.columns:
    df_vendedores_filtrado = df_vendedores_filtrado[
        df_vendedores_filtrado['estado'] == estado
    ]

# salvar estado
st.session_state["data_range"] = data_range
st.session_state["estado"] = estado
st.session_state["cidade"] = cidade
st.session_state["categoria"] = categoria

# -----------------------------
# 🔥 FILTRO GLOBAL REAL (FATO)
# -----------------------------
df_fato_filtrado = df_fato.copy()

# DATA
if isinstance(data_range, tuple) and len(data_range) == 2:
    data_inicio = pd.to_datetime(data_range[0])
    data_fim = pd.to_datetime(data_range[1])

    df_fato_filtrado = df_fato_filtrado[
        (df_fato_filtrado['mes'] >= data_inicio) &
        (df_fato_filtrado['mes'] <= data_fim)
    ]

# ESTADO
if estado != "Todos":
    df_fato_filtrado = df_fato_filtrado[
        df_fato_filtrado['estado'] == estado
    ]

# CIDADE
if cidade != "Todas":
    df_fato_filtrado = df_fato_filtrado[
        df_fato_filtrado['cidade'] == cidade
    ]

# CATEGORIA
if categoria != "Todas":
    df_fato_filtrado = df_fato_filtrado[
        df_fato_filtrado['categoria'] == categoria
    ]
    
# DF_Filtrado
df_filtrado = (
    df_fato_filtrado.groupby('mes')['receita']
    .sum()
    .reset_index()
)

df_pedidos_filtrado = (
    df_fato_filtrado.groupby('mes')['order_id']
    .nunique()
    .reset_index()
)

df_pedidos_filtrado.columns = ['mes', 'qtd_pedidos']

df_ticket_filtrado = df_filtrado.copy()
df_ticket_filtrado['ticket_medio'] = (
    df_filtrado['receita'] / 
    df_pedidos_filtrado['qtd_pedidos']
)

# -----------------------------
# FILTRO GEO
# -----------------------------
df_geo_filtrado = df_geo.copy()

if estado != "Todos":
    df_geo_filtrado = df_geo_filtrado[df_geo_filtrado['estado'] == estado]

if cidade != "Todas":
    df_geo_filtrado = df_geo_filtrado[df_geo_filtrado['cidade'] == cidade]

# -----------------------------
# FILTRO CATEGORIA (NOVO)
# -----------------------------
df_produtos_filtrado = df_produtos.copy()

if categoria != "Todas":
    df_produtos_filtrado = df_produtos_filtrado[df_produtos_filtrado['categoria'] == categoria]


# -----------------------------
# ABAS
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Receita & Performance",
    "🚚 Logística",
    "📍 Geográfico",
    "🏪 Vendedores",
    "🛒 Produtos",
])

# =====================================================
# 📊 ABA 1 — RECEITA & PERFORMANCE (PROFISSIONAL)
# =====================================================
with tab1:

    st.subheader("📊 Visão Geral de Performance")

    receita_total = df_filtrado['receita'].sum()
    total_pedidos = df_pedidos_filtrado['qtd_pedidos'].sum()
    ticket = receita_total / total_pedidos if total_pedidos > 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Receita Total", f"R$ {receita_total:,.2f}")
    col2.metric("📦 Pedidos", int(total_pedidos))
    col3.metric("💳 Ticket Médio", f"R$ {ticket:,.2f}")

    import plotly.express as px

    # -----------------------------
    # RECEITA
    # -----------------------------
    st.subheader("📈 Evolução da Receita")

    fig_receita = px.line(
        df_filtrado,
        x='mes',
        y='receita',
        title="Receita ao longo do tempo"
    )

    st.plotly_chart(fig_receita, use_container_width=True)

    # -----------------------------
    # PEDIDOS
    # -----------------------------
    st.subheader("📦 Evolução dos Pedidos")

    fig_pedidos = px.line(
        df_pedidos_filtrado,
        x='mes',
        y='qtd_pedidos',
        title="Quantidade de pedidos ao longo do tempo"
    )

    st.plotly_chart(fig_pedidos, use_container_width=True)

    # -----------------------------
    # TICKET
    # -----------------------------
    st.subheader("💳 Evolução do Ticket Médio")

    fig_ticket = px.line(
        df_ticket_filtrado,
        x='mes',
        y='ticket_medio',
        title="Ticket médio ao longo do tempo"
    )

    st.plotly_chart(fig_ticket, use_container_width=True)
    
    # -----------------------------
    # 📊 TENDÊNCIA (MÉDIA MÓVEL)
    # -----------------------------
    st.subheader("📊 Tendência da Receita (Média Móvel)")

    import plotly.graph_objects as go

    df_trend = df_filtrado.copy()

    # média móvel de 3 meses
    df_trend['media_movel'] = df_trend['receita'].rolling(3).mean()

    fig = go.Figure()

    # receita real
    fig.add_trace(go.Scatter(
        x=df_trend['mes'],
        y=df_trend['receita'],
        name='Receita',
        mode='lines+markers'
    ))

    # tendência
    fig.add_trace(go.Scatter(
        x=df_trend['mes'],
        y=df_trend['media_movel'],
        name='Tendência (Média Móvel)',
        mode='lines',
        line=dict(width=3)
    ))

    fig.update_layout(
        title="Receita vs Tendência (Média Móvel)",
        xaxis_title="Data",
        yaxis_title="Receita"
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # -----------------------------
    # 🧠 INSIGHTS AUTOMÁTICOS
    # -----------------------------
    st.subheader("🧠 Insights do Negócio")

    crescimento = df_filtrado['receita'].pct_change().mean() * 100

    if crescimento > 5:
        st.success("🚀 Receita em crescimento consistente")

    elif crescimento < -5:
        st.error("📉 Queda relevante na receita")

    else:
        st.info("📊 Receita estável")
    
# =====================================================
# 🚚 ABA 2 — LOGÍSTICA + SATISFAÇÃO (CORRIGIDA)
# =====================================================
with tab2:

    st.subheader("🚚 Logística & Experiência do Cliente")

    import plotly.express as px

    # -----------------------------
    # KPIs
    # -----------------------------
    tempo_medio = df_entrega['tempo_entrega_dias'].mean()
    atraso = df_entrega['atraso'].mean() * 100
    nota_media = df_reviews['review_score'].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("🚚 Tempo Médio", f"{tempo_medio:.2f} dias")
    col2.metric("⏱️ % Atraso", f"{atraso:.2f}%")
    col3.metric("⭐ Nota Média", f"{nota_media:.2f}")

    # -----------------------------
    # DISTRIBUIÇÃO ENTREGA
    # -----------------------------
    st.subheader("📊 Distribuição do Tempo de Entrega")

    df_plot = df_entrega[df_entrega['tempo_entrega_dias'] < 40].copy()

    fig = px.histogram(
        df_plot,
        x='tempo_entrega_dias',
        nbins=30,
        histnorm='probability density',
        title="Distribuição dos Dias de Entrega"
    )

    media = df_plot['tempo_entrega_dias'].mean()

    fig.add_vline(
        x=media,
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text=f"Média: {media:.2f} dias",
        annotation_position="top right"
    )

    fig.update_layout(
        bargap=0.2,
        hovermode='x unified',
        xaxis_title="Dias",
        yaxis_title="Densidade"
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # FAIXAS ENTREGA
    # -----------------------------
    st.subheader("📦 Entregas por Faixa")

    df_plot['faixa'] = pd.cut(
        df_plot['tempo_entrega_dias'],
        bins=[0,5,10,15,20,30,40],
        labels=["0-5","5-10","10-15","15-20","20-30","30+"]
    )

    faixa_dist = df_plot['faixa'].value_counts().sort_index().reset_index()
    faixa_dist.columns = ['faixa', 'quantidade']

    fig_faixa = px.bar(
        faixa_dist,
        x='faixa',
        y='quantidade'
    )

    st.plotly_chart(fig_faixa, use_container_width=True)

    # -----------------------------
    # ⭐ IMPACTO DO ATRASO
    # -----------------------------
    st.subheader("⭐ Impacto do Atraso na Avaliação")

    atraso_review = df_reviews.groupby('atraso')['review_score'].mean().reset_index()
    atraso_review['status'] = atraso_review['atraso'].map({0: "No prazo", 1: "Atrasado"})

    fig_atraso = px.bar(
        atraso_review,
        x='status',
        y='review_score',
        color='status'
    )

    st.plotly_chart(fig_atraso, use_container_width=True)

    # -----------------------------
    # 📈 SATISFAÇÃO POR TEMPO
    # -----------------------------
    st.subheader("📈 Avaliação Média por Tempo de Entrega")

    df_reviews_plot = df_reviews[df_reviews['tempo_entrega_dias'] < 40].copy()

    df_reviews_plot['faixa'] = pd.cut(
        df_reviews_plot['tempo_entrega_dias'],
        bins=[0,5,10,15,20,30,40],
        labels=["0-5","5-10","10-15","15-20","20-30","30+"]
    )

    faixa_review = df_reviews_plot.groupby('faixa')['review_score'].mean().reset_index()

    fig_review = px.line(
        faixa_review,
        x='faixa',
        y='review_score',
        markers=True
    )

    st.plotly_chart(fig_review, use_container_width=True)
    
    # -----------------------------
    # ⚠️ ALERTA OPERACIONAL
    # -----------------------------
    if atraso > 15:
        st.error("🚨 Alto índice de atraso — risco na experiência do cliente")

    if nota_media < 3.5:
        st.warning("⚠️ Nota média baixa — possível insatisfação do cliente")

    if tempo_medio > 12:
        st.warning("⏱️ Tempo de entrega elevado")

# =====================================================
# 📍 ABA 3 — GEOGRÁFICO INTERATIVO
# =====================================================
with tab3:

    st.subheader("📍 Análise Geográfica")

    # -----------------------------
    # PARETO INTERATIVO
    # -----------------------------
    st.subheader("📊 Pareto de Receita por Estado")

    pareto = (
        df_geo_filtrado.groupby('estado')['receita']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    pareto['acumulado'] = pareto['receita'].cumsum()
    pareto['percentual'] = pareto['acumulado'] / pareto['receita'].sum()

    import plotly.graph_objects as go

    fig = go.Figure()

    # barras
    fig.add_bar(
        x=pareto['estado'],
        y=pareto['receita'],
        name='Receita',
        yaxis='y1'
    )

    # linha percentual
    fig.add_trace(go.Scatter(
        x=pareto['estado'],
        y=pareto['percentual'],
        name='Percentual acumulado',
        yaxis='y2',
        mode='lines+markers'
    ))

    # layout com dois eixos
    fig.update_layout(
        yaxis=dict(title='Receita'),
        yaxis2=dict(
            title='Percentual acumulado',
            overlaying='y',
            side='right',
            tickformat=".0%"
        ),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # TOP CIDADES INTERATIVO
    # -----------------------------
    st.subheader("🏙️ Top Cidades por Receita")

    import plotly.express as px

    top_cidades = df_geo_filtrado.sort_values('receita', ascending=False).head(10)

    fig_cidades = px.bar(
        top_cidades,
        x='cidade',
        y='receita',
        hover_data=['estado', 'pedidos', 'ticket_medio']
    )

    st.plotly_chart(fig_cidades, use_container_width=True)

    # -----------------------------
    # TABELA
    # -----------------------------
    with st.expander("Ver dados geográficos"):
        st.dataframe(df_geo_filtrado)
        

    # -----------------------------
    # TICKET MÉDIO POR ESTADO
    # -----------------------------
    st.subheader("💳 Ticket Médio por Estado")

    import plotly.express as px

    ticket_estado = (
        df_geo_filtrado.groupby('estado')['ticket_medio']
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig_ticket = px.bar(
        ticket_estado,
        x='estado',
        y='ticket_medio',
        hover_data=['ticket_medio']
    )

    st.plotly_chart(fig_ticket, use_container_width=True)
    
# =====================================================
# 🏪 ABA 4 — VENDEDORES
# =====================================================
with tab4:

    st.subheader("🏪 Performance de Vendedores")

    import plotly.express as px

    # -----------------------------
    # KPIs
    # -----------------------------
    total_vendedores = df_vendedores_filtrado['seller_id'].nunique()
    receita_total = df_vendedores_filtrado['receita'].sum()

    col1, col2 = st.columns(2)

    col1.metric("🏪 Total de Vendedores", total_vendedores)
    col2.metric("💰 Receita Total", f"R$ {receita_total:,.2f}")

    # -----------------------------
    # TOP VENDEDORES
    # -----------------------------
    st.subheader("🏆 Top 10 Vendedores por Receita")

    top_vendedores = df_vendedores_filtrado.sort_values('receita', ascending=False).head(10)

    fig_top = px.bar(
        top_vendedores,
        x='seller_id',
        y='receita',
        hover_data=['pedidos', 'ticket_medio']
    )

    st.plotly_chart(fig_top, use_container_width=True)
    
    top1 = df_vendedores_filtrado.sort_values('receita', ascending=False).iloc[0]
    participacao = top1['receita'] / df_vendedores_filtrado['receita'].sum()

    if participacao > 0.3:
        st.warning("⚠️ Forte dependência de um único vendedor")

    else:
        st.success("✅ Receita bem distribuída entre vendedores")

    # -----------------------------
    # 📊 DISTRIBUIÇÃO DE VENDEDORES
    # -----------------------------
    st.subheader("📊 Distribuição de Vendedores por Receita")

    import plotly.express as px

    df_dist = df_vendedores_filtrado.copy()

    df_dist['faixa_receita'] = pd.cut(
        df_dist['receita'],
        bins=[0,1000,5000,10000,50000,100000,1000000],
        labels=[
            "0-1k",
            "1k-5k",
            "5k-10k",
            "10k-50k",
            "50k-100k",
            "100k+"
        ]
    )

    dist = df_dist['faixa_receita'].value_counts().sort_index().reset_index()
    dist.columns = ['faixa', 'quantidade']

    fig = px.bar(
        dist,
        x='faixa',
        y='quantidade',
        title="Distribuição de Vendedores por Faixa de Receita",
        hover_data=['quantidade']
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # -----------------------------
    # 🔎 FILTRO INTERATIVO POR FAIXA
    # -----------------------------
    st.subheader("🔎 Explorar vendedores por faixa")

    faixa_selecionada = st.selectbox(
        "Selecione a faixa de receita",
        dist['faixa']
    )

    # filtrar dados
    df_filtrado_faixa = df_dist[df_dist['faixa_receita'] == faixa_selecionada]

    st.write(f"Total de vendedores: {len(df_filtrado_faixa)}")

    # mostrar tabela
    st.dataframe(
        df_filtrado_faixa[['seller_id', 'receita', 'pedidos', 'ticket_medio']]
        .sort_values('receita', ascending=False)
    )

# =====================================================
# 🛒 ABA 5 — PRODUTOS
# =====================================================
with tab5:

    st.subheader("🛒 Análise de Produtos")

    import plotly.express as px

    # -----------------------------
    # KPIs
    # -----------------------------
    total_categorias = df_produtos_filtrado['categoria'].nunique()
    receita_total = df_produtos_filtrado['receita'].sum()

    col1, col2 = st.columns(2)

    col1.metric("🛒 Total de Categorias", total_categorias)
    col2.metric("💰 Receita Total", f"R$ {receita_total:,.2f}")

    # -----------------------------
    # TOP CATEGORIAS
    # -----------------------------
    st.subheader("🏆 Top Categorias por Receita")

    top_cat = df_produtos_filtrado.sort_values('receita', ascending=False).head(10)

    fig_top = px.bar(
        top_cat,
        x='categoria',
        y='receita',
        hover_data=['pedidos', 'ticket_medio']
    )

    st.plotly_chart(fig_top, use_container_width=True)
    
    # -----------------------------
    # 📊 CONCENTRAÇÃO DE RECEITA
    # -----------------------------
    st.subheader("📊 Concentração de Receita (Pareto)")

    pareto_cat = (
        df_produtos_filtrado
        .sort_values('receita', ascending=False)
        .reset_index(drop=True)
    )

    pareto_cat['acumulado'] = pareto_cat['receita'].cumsum()
    pareto_cat['percentual'] = pareto_cat['acumulado'] / pareto_cat['receita'].sum()

    top_20 = pareto_cat[pareto_cat['percentual'] <= 0.8]

    st.info(
        f"📌 {len(top_20)} categorias representam 80% da receita"
    )

    # -----------------------------
    # DISTRIBUIÇÃO (CORRIGIDA)
    # -----------------------------
    st.subheader("📊 Distribuição por Faixa de Receita")

    df_dist = df_produtos_filtrado.copy()

    df_dist['faixa'] = pd.cut(
        df_dist['receita'],
        bins=[0,1000,5000,10000,50000,100000,1000000,float('inf')],
        labels=[
            "0-1k",
            "1k-5k",
            "5k-10k",
            "10k-50k",
            "50k-100k",
            "100k-1M",
            "1M+"
        ]
    )

    # garantir ordem correta
    dist = df_dist['faixa'].value_counts().sort_index().reset_index()
    dist.columns = ['faixa', 'quantidade']

    fig_dist = px.bar(
        dist,
        x='faixa',
        y='quantidade',
        title="Distribuição de Categorias por Receita"
    )

    st.plotly_chart(fig_dist, use_container_width=True)

    # -----------------------------
    # 🔎 DRILL-DOWN (MELHORADO)
    # -----------------------------
    st.subheader("🔎 Explorar categorias")

    faixa_sel = st.selectbox(
        "Selecione a faixa",
        dist['faixa'].dropna()
    )

    df_filtro = df_dist[df_dist['faixa'] == faixa_sel]

    st.write(f"Total de categorias: {len(df_filtro)}")

    st.dataframe(
        df_filtro[['categoria', 'receita', 'pedidos', 'ticket_medio']]
        .sort_values('receita', ascending=False)
    )

        
    
