# utils_contas.py

import streamlit as st
import pandas as pd
import plotly.express as px
import locale
import re

# Função para garantir que o locale esteja configurado
def configurar_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL, '')

def formatar_moeda(valor):
    try:
        return locale.currency(valor, grouping=True, symbol='R$')
    except (TypeError, ValueError): return "N/A"

# Função que busca por palavras chave comuns e retorna um df com resultados
def analisar_palavras_chave(df):
    palavras = [
        'uber', 'iptu', 'internet', 'multa', 'sítio', 'manutenção', 'manutencao',
        'encargos', 'gasolina', 'títulos', 'titulo', 'gás', 'juros', 'marketing', 
        'frete', 'passagem', 'viagem', 'aluguel', 'condominio', 'telefone'
    ]
    resultados = {}
    for palavra in palavras:
        df_palavra = df[df['descricao'].str.contains(palavra, flags=re.IGNORECASE, regex=True, na=False)]
        if not df_palavra.empty:
            resultados[palavra.capitalize()] = {'Ocorrências': len(df_palavra), 'Valor Total': df_palavra['valor_pago'].sum()}
    if resultados:
        return pd.DataFrame.from_dict(resultados, orient='index').sort_values(by='Valor Total', ascending=False)
    return pd.DataFrame()

@st.cache_data
def carregar_dados_contas(arquivo_enviado):
    try:
        df = pd.read_excel(arquivo_enviado, sheet_name='Contas pagas', header=2)
        indices = [0, 1, 2, 5, 6, 7, 8, 9, 10, 11]
        df_selecionado = df.iloc[:, indices].copy()
        nomes = ['empresa', 'centro_de_custo', 'fornecedor', 'descricao', 'valor', 'valor_pago', 'juros', 'data_vencimento', 'data_pagamento', 'forma_pagamento']
        df_selecionado.columns = nomes
        for col in ['valor', 'valor_pago', 'juros']: df_selecionado[col] = pd.to_numeric(df_selecionado[col], errors='coerce').fillna(0)
        for col in ['data_vencimento', 'data_pagamento']: df_selecionado[col] = pd.to_datetime(df_selecionado[col], errors='coerce').dt.date
        return df_selecionado.dropna(subset=['empresa'])
    except Exception:
        return None

# ---- ESTA É A FUNÇÃO QUE DESENHA A PÁGINA INTEIRA ----
def renderizar_pagina_contas_pagas(df_pagas):
    configurar_locale()
    
    st.header("Análise Inteligente de Contas Pagas")
    
    # Filtros na barra lateral
    st.sidebar.header("Filtros para Contas Pagas")
    opcoes_empresa = ['TODAS'] + sorted(df_pagas['empresa'].unique().tolist())
    empresa_selecionada = st.sidebar.selectbox("Empresa:", opcoes_empresa)
    opcoes_custo = ['TODAS'] + sorted(df_pagas['centro_de_custo'].unique().tolist())
    centro_custo_selecionado = st.sidebar.selectbox("Centro de Custo:", opcoes_custo)
    
    # Aplica os filtros
    df_filtrado = df_pagas.copy()
    if empresa_selecionada != 'TODAS': df_filtrado = df_filtrado[df_filtrado['empresa'] == empresa_selecionada]
    if centro_custo_selecionado != 'TODAS': df_filtrado = df_filtrado[df_filtrado['centro_de_custo'] == centro_custo_selecionado]

    # Mostra o cabeçalho dos resultados
    st.subheader(f"Resultados para: {empresa_selecionada} | {centro_custo_selecionado}")
    
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # ---- SEÇÃO DE KPIs ----
        total_pago = df_filtrado['valor_pago'].sum()
        num_transacoes = len(df_filtrado)
        ticket_medio = df_filtrado['valor_pago'].mean()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Valor Total Pago", formatar_moeda(total_pago))
        kpi2.metric("Nº de Transações", f"{num_transacoes:,}")
        kpi3.metric("Ticket Médio", formatar_moeda(ticket_medio))

        # ---- GRÁFICO DE EVOLUÇÃO ----
        st.markdown("---")
        st.subheader("📈 Evolução dos Gastos Diários")
        gastos_diarios = df_filtrado.groupby('data_pagamento')['valor_pago'].sum()
        st.line_chart(gastos_diarios)

        # ---- SEÇÃO DE ANÁLISES DETALHADAS ----
        st.markdown("---")
        st.header("Análises Detalhadas dos Gastos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💡 Top Gastos por Palavra-Chave")
            df_palavras = analisar_palavras_chave(df_filtrado)
            if not df_palavras.empty:
                df_palavras['Valor Total'] = df_palavras['Valor Total'].apply(formatar_moeda)
                st.dataframe(df_palavras)
            else:
                st.info("Nenhuma palavra-chave comum foi encontrada.")

        with col2:
            st.subheader("👥 Top 10 Fornecedores por Valor")
            top_fornecedores = df_filtrado.groupby('fornecedor').agg(
                valor_pago_total=('valor_pago', 'sum'),
                ocorrencias=('valor_pago', 'count')
            ).nlargest(10, 'valor_pago_total')
            top_fornecedores['valor_pago_total'] = top_fornecedores['valor_pago_total'].apply(formatar_moeda)
            st.dataframe(top_fornecedores)

        # ---- SEÇÃO DE GRÁFICOS GERAIS ----
        st.markdown("---")
        st.subheader("Visão Geral em Gráficos")
        
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            st.write("Gastos por Centro de Custo")
            gastos_por_custo = df_filtrado.groupby('centro_de_custo')['valor_pago'].sum().nlargest(10).sort_values(ascending=False)
            st.bar_chart(gastos_por_custo)
            
        with g_col2:
            st.write("Gastos por Forma de Pagamento")
            gastos_por_forma = df_filtrado.groupby('forma_pagamento')['valor_pago'].sum()
            fig_forma = px.pie(gastos_por_forma, values='valor_pago', names=gastos_por_forma.index, hole=.3)
            st.plotly_chart(fig_forma, use_container_width=True)