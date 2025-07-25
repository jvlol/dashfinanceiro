# app.py

import streamlit as st

# Importa as funções dos nossos arquivos de utilidades
from utils_contas import renderizar_pagina_contas_pagas, carregar_dados_contas
from utils_fluxo import renderizar_pagina_fluxo_caixa, carregar_fluxo_de_caixa
from utils_entradas import renderizar_pagina_entradas, carregar_dados_entradas # <-- NOVA IMPORTAÇÃO

# --- INTERFACE PRINCIPAL ---
st.set_page_config(layout="wide", page_title="Dashboard Financeiro")
st.title("📊 Dashboard Financeiro")
st.markdown("---")

# Widget de upload
uploaded_file = st.file_uploader(
    "Comece fazendo o upload da sua planilha Excel", 
    type="xlsx", 
    key="main_uploader"
)

if uploaded_file is not None:
    
    # Menu de seleção de análise
    st.sidebar.title("Menu de Análise")
    tipo_analise = st.sidebar.radio(
        "Escolha qual análise deseja visualizar:",
        ('Análise de Contas Pagas', 'Fluxo de Caixa', 'Análise de Entradas') # <-- NOVA OPÇÃO
    )
    
    # Lógica para renderizar a "página" selecionada
    if tipo_analise == 'Análise de Contas Pagas':
        df_contas = carregar_dados_contas(uploaded_file)
        if df_contas is not None:
            renderizar_pagina_contas_pagas(df_contas)
        else:
            st.error("A aba 'Contas pagas' não foi encontrada ou está em um formato inesperado na planilha.")
            
    elif tipo_analise == 'Fluxo de Caixa':
        df_fluxo = carregar_fluxo_de_caixa(uploaded_file)
        if df_fluxo is not None:
            renderizar_pagina_fluxo_caixa(df_fluxo)
        else:
            st.error("A aba 'Entrada x  Saída' não foi encontrada ou está em um formato inesperado na planilha.")

    elif tipo_analise == 'Análise de Entradas': # <-- NOVO BLOCO LÓGICO
        dados_entradas = carregar_dados_entradas(uploaded_file)
        if dados_entradas is not None:
            renderizar_pagina_entradas(dados_entradas)
        else:
            st.error("A aba 'Entradas' não foi encontrada ou está em um formato inesperado na planilha.")
else:
    st.info("Aguardando o upload da planilha para iniciar as análises.")