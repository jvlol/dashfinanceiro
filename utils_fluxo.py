# utils_fluxo.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import locale

# Funções auxiliares
def configurar_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL, '')

def formatar_moeda(valor):
    try:
        return locale.currency(valor, grouping=True, symbol='R$')
    except (TypeError, ValueError): return "N/A"

@st.cache_data
def carregar_fluxo_de_caixa(arquivo_enviado):
    try:
        # Lê a aba inteira, permitindo que a gente encontre a tabela dinamicamente
        df_completo = pd.read_excel(arquivo_enviado, sheet_name='Entrada x  Saída', header=None)

        # 1. Encontrar onde a tabela começa
        start_row = -1
        for i, row in df_completo.iterrows():
            if "EMPRESA" in str(row.values):
                start_row = i
                break
        
        if start_row == -1:
            st.warning("Não foi possível encontrar a linha de cabeçalho 'EMPRESA' na aba.")
            return None

        # 2. Ler o excel novamente, mas agora usando a linha correta como cabeçalho
        df_fluxo = pd.read_excel(arquivo_enviado, sheet_name='Entrada x  Saída', header=start_row)
        
        # 3. Remover linhas completamente vazias
        df_fluxo.dropna(how='all', inplace=True)
        df_fluxo = df_fluxo[df_fluxo['EMPRESA'].notna()]
        
        # --- A CORREÇÃO PRINCIPAL ESTÁ AQUI ---
        # 4. Seleciona apenas as 5 primeiras colunas para garantir que temos a estrutura certa
        colunas_esperadas = ['EMPRESA', 'SALDO ANTERIOR', 'ENTRADA', 'SAÍDA', 'TOTAL']
        # Pega as colunas do df que batem com nossa lista, ignorando outras
        df_fluxo = df_fluxo[colunas_esperadas]
        
        # 5. Renomeia para nomes padronizados (agora o tamanho vai bater)
        df_fluxo.columns = ['empresa', 'saldo_anterior', 'entrada', 'saida', 'total']
        
        # 6. Converte as colunas para formato numérico
        for col in ['saldo_anterior', 'entrada', 'saida', 'total']:
            df_fluxo[col] = pd.to_numeric(df_fluxo[col], errors='coerce').fillna(0)
            
        return df_fluxo
        
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao ler a aba 'Entrada x  Saída': {e}")
        return None


# --- Função que desenha a interface do Fluxo de Caixa ---
def renderizar_pagina_fluxo_caixa(df_fluxo):
    configurar_locale()
    
    st.header("Fluxo de Caixa (Entradas e Saídas)")

    if df_fluxo is None or df_fluxo.empty:
        st.warning("Nenhum dado válido foi encontrado na aba de Fluxo de Caixa.")
        return

    # Extrai a linha de totais
    df_detalhe = df_fluxo[df_fluxo['empresa'].str.lower() != 'total'].copy()
    if 'total' in df_fluxo['empresa'].str.lower().values:
        totais = df_fluxo[df_fluxo['empresa'].str.lower() == 'total'].iloc[0]
    else:
        # Se não houver linha 'Total', calcula na hora
        totais = df_detalhe.sum(numeric_only=True)
        totais['empresa'] = 'Total Calculado'

    saldo_anterior = totais['saldo_anterior']
    entradas_total = totais['entrada']
    saidas_total = totais['saida']
    saldo_final = totais['total']

    # Seção de KPIs
    st.subheader("Resumo Financeiro Total")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Anterior Total", formatar_moeda(saldo_anterior))
    col2.metric("Total de Entradas", formatar_moeda(entradas_total))
    col3.metric("Total de Saídas", formatar_moeda(saidas_total), delta_color="inverse")
    col4.metric("Saldo Final Calculado", formatar_moeda(saldo_final))
    
    # Gráfico de Cascata
    st.subheader("Composição do Saldo Final")
    fig_waterfall = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["absolute", "relative", "relative", "total"],
        x = ["Saldo Anterior", "Entradas", "Saídas", "Saldo Final"],
        text = [formatar_moeda(v) for v in [saldo_anterior, entradas_total, -saidas_total, saldo_final]],
        y = [saldo_anterior, entradas_total, -saidas_total, 0],
    ))
    st.plotly_chart(fig_waterfall, use_container_width=True)

    # Tabela de Detalhes
    st.subheader("Detalhamento por Conta/Empresa")
    st.dataframe(df_detalhe.style.format(formatter=formatar_moeda, subset=['saldo_anterior', 'entrada', 'saida', 'total']))