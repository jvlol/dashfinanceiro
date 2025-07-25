# utils_entradas.py

import streamlit as st
import pandas as pd
import locale
import plotly.express as px # Importando Plotly Express

# --- Funções Auxiliares (sem alteração) ---
def configurar_locale():
    try: locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except: locale.setlocale(locale.LC_ALL, '')

def formatar_moeda(valor):
    try: return locale.currency(valor, grouping=True, symbol='R$')
    except (TypeError, ValueError): return "N/A"

# A função de carga permanece a mesma (já está otimizada)
@st.cache_data
def carregar_dados_entradas(arquivo_enviado):
    # (Mantenha o código da função carregar_dados_entradas aqui, ele não muda)
    try:
        df_full = pd.read_excel(arquivo_enviado, sheet_name='Entradas', header=2)
        df_full.dropna(how='all', inplace=True)
        df_full.columns = df_full.columns.astype(str)
        df_full.rename(columns={df_full.columns[0]: 'Referencia'}, inplace=True)
        
        df_sumario = df_full[df_full['Referencia'].astype(str).str.contains('Entrada|Saída|Saldo', case=False, na=False)].tail(3)
        df_transacoes = df_full[pd.to_datetime(df_full['Referencia'], errors='coerce').notna()].copy()
        
        df_transacoes.rename(columns={'Referencia': 'data'}, inplace=True)
        df_transacoes['data'] = pd.to_datetime(df_transacoes['data'])
        for col in df_transacoes.columns.drop('data'):
            df_transacoes[col] = pd.to_numeric(df_transacoes[col], errors='coerce').fillna(0)

        return {'transacoes': df_transacoes, 'sumario': df_sumario}
    except Exception as e:
        st.error(f"Erro ao carregar a aba 'Entradas': {e}")
        return None


# --- Função de Renderização (AQUI ESTÃO AS MUDANÇAS DE DESIGN) ---
def renderizar_pagina_entradas(dados):
    configurar_locale()
    
    df_transacoes = dados['transacoes']
    df_sumario = dados['sumario']

    st.title("Análise Completa de Entradas")
    
    # (A Seção 1 - Resumo do Mês - pode ser mantida como estava, ela já está boa)
    # ... (Cole aqui o código da Seção 1 se desejar manter o Resumo Geral)

    st.markdown("---")
    
    # --- SEÇÃO 2: FERRAMENTA DE ANÁLISE DINÂMICA (DESIGN MODERNO) ---
    st.header("🔬 Ferramenta de Análise Dinâmica")
    
    # Configuração dos Filtros na Sidebar
    st.sidebar.header("Filtros Dinâmicos")
    fontes_disponiveis = sorted([col for col in df_transacoes.columns if col not in ['data', 'Total']])
    opcoes_com_todos = ['TODAS'] + fontes_disponiveis
    fontes_selecionadas_ui = st.sidebar.multiselect(
        "Fontes de Entrada:", options=opcoes_com_todos, default=['TODAS']
    )

    if 'TODAS' in fontes_selecionadas_ui:
        fontes_selecionadas = fontes_disponiveis
    else:
        fontes_selecionadas = fontes_selecionadas_ui
        
    data_min, data_max = df_transacoes['data'].min().date(), df_transacoes['data'].max().date()
    filtro_data_inicio, filtro_data_fim = st.sidebar.date_input(
        "Período de Análise:", value=(data_min, data_max), min_value=data_min, max_value=data_max
    )
    
    # Lógica de Filtragem
    df_filtrado = df_transacoes[
        (df_transacoes['data'].dt.date >= filtro_data_inicio) & (df_transacoes['data'].dt.date <= filtro_data_fim)
    ]
    
    if not fontes_selecionadas or df_filtrado.empty:
        st.warning("Selecione fontes e um período com dados para analisar.")
    else:
        total_filtrado = df_filtrado[fontes_selecionadas].sum().sum()
        df_filtrado['Soma Diária Selecionada'] = df_filtrado[fontes_selecionadas].sum(axis=1)

        # --- PAINEL DE PERFORMANCE COM DESIGN DE CARDS (CONTAINERS) ---
        
        # Cálculos dos KPIs (sem alteração)
        dias_com_atividade = df_filtrado[df_filtrado['Soma Diária Selecionada'] > 0]['data'].nunique()
        media_diaria = total_filtrado / dias_com_atividade if dias_com_atividade > 0 else 0
        melhor_dia_data = df_filtrado.loc[df_filtrado['Soma Diária Selecionada'].idxmax()]['data'].date()
        melhor_dia_valor = df_filtrado['Soma Diária Selecionada'].max()
        melhor_fonte_nome = df_filtrado[fontes_selecionadas].sum().idxmax()

        # Usando st.container com borda para criar um "card"
        with st.container(border=True):
            st.subheader("Painel de Performance (Filtro Aplicado)")
            
            # KPI Principal
            st.metric(label="Total de Entradas (Filtro)", value=formatar_moeda(total_filtrado))
            
            # KPIs Secundários
            k1, k2, k3 = st.columns(3)
            k1.metric("🗓️ Dias com Entradas", f"{dias_com_atividade} dias")
            k2.metric("📊 Média por Dia Ativo", formatar_moeda(media_diaria))
            k3.metric("🏆 Melhor Fonte", melhor_fonte_nome)

            k4, k5 = st.columns(2)
            k4.metric("🚀 Dia de Pico", melhor_dia_data.strftime('%d/%m/%Y'))
            k5.metric("💰 Valor do Pico", formatar_moeda(melhor_dia_valor))

        st.markdown("---")

        # --- GRÁFICOS MODERNOS (PLOTLY) ---
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            # Gráfico de Linha com Plotly
            fig_line = px.line(
                df_filtrado, 
                x='data', 
                y='Soma Diária Selecionada', 
                title="Evolução Diária das Entradas Selecionadas",
                markers=True # Adiciona pontos nos dias
            )
            fig_line.update_layout(yaxis_title="Valor (R$)", xaxis_title="Data")
            st.plotly_chart(fig_line, use_container_width=True)

        with col_graf2:
            # Gráfico de Ranking com Plotly (Barras Horizontais)
            ranking = df_filtrado[fontes_selecionadas].sum().sort_values(ascending=True)
            fig_bar = px.bar(
                ranking, 
                orientation='h', 
                title="Ranking de Desempenho no Período",
                text=ranking.apply(formatar_moeda) # Mostra o valor formatado na barra
            )
            fig_bar.update_layout(yaxis_title="Fonte de Entrada", xaxis_title="Total Faturado (R$)")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("Tabela de Dados Detalhados (Filtro Aplicado)")
        colunas_tabela = ['data'] + fontes_selecionadas
        st.dataframe(df_filtrado[colunas_tabela])