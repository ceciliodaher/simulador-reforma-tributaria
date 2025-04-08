import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import base64
from io import BytesIO
from datetime import datetime

# Importar nossas classes e funções customizadas
from config import ConfiguracaoTributaria
from calculadoras import CalculadoraTributosAtuais, CalculadoraIVADual
from utils import (formatar_br, criar_grafico_comparativo, criar_grafico_aliquotas,
                   criar_grafico_transicao, criar_grafico_incentivos)

# Configuração da página
st.set_page_config(
    page_title="Simulador da Reforma Tributária",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Função para inicializar a sessão
def inicializar_sessao():
    if 'config' not in st.session_state:
        st.session_state.config = ConfiguracaoTributaria()

    if 'calculadora_iva' not in st.session_state:
        st.session_state.calculadora_iva = CalculadoraIVADual(st.session_state.config)

    if 'resultados' not in st.session_state:
        st.session_state.resultados = {}

    if 'aliquotas_equivalentes' not in st.session_state:
        st.session_state.aliquotas_equivalentes = {}

    if 'memoria_calculo' not in st.session_state:
        st.session_state.memoria_calculo = {}


# Função para adicionar incentivo
def adicionar_incentivo(tipo, dados):
    """Adiciona um novo incentivo fiscal à configuração."""
    descricao = dados.get("descricao", f"Incentivo {tipo.capitalize()}")
    tipo_incentivo = dados.get("tipo", "Nenhum")
    percentual = dados.get("percentual", 0) / 100
    perc_operacoes = dados.get("perc_operacoes", 100) / 100

    if tipo_incentivo != "Nenhum" and percentual <= 0:
        st.error("O percentual do incentivo deve ser maior que zero.")
        return False

    # Validar total de operações incentivadas (não aplicável para incentivos de apuração)
    if tipo != "apuracao":
        incentivos = st.session_state.config.icms_config[f"incentivos_{tipo}"]
        total_percentual = perc_operacoes

        for inc in incentivos:
            total_percentual += inc.get("percentual_operacoes", 0)

        if total_percentual > 1:
            st.error(f"O total de operações incentivadas ({formatar_br(total_percentual * 100)}%) excede 100%. "
                     "Ajuste os percentuais para que a soma não ultrapasse 100%.")
            return False

    # Criar objeto de incentivo
    incentivo = {
        "descricao": descricao,
        "tipo": tipo_incentivo,
        "percentual": percentual,
        "percentual_operacoes": perc_operacoes,
        "aplicavel_saidas": tipo == "saida",
        "aplicavel_entradas": tipo == "entrada",
        "aplicavel_apuracao": tipo == "apuracao"
    }

    # Adicionar à configuração
    st.session_state.config.icms_config[f"incentivos_{tipo}"].append(incentivo)
    return True


# Função para remover incentivo
def remover_incentivo(tipo, indice):
    """Remove um incentivo fiscal da configuração."""
    if 0 <= indice < len(st.session_state.config.icms_config[f"incentivos_{tipo}"]):
        st.session_state.config.icms_config[f"incentivos_{tipo}"].pop(indice)
        return True
    return False


# Função para exportar resultados
def exportar_resultados(formato):
    """Exporta os resultados para o formato especificado."""
    if not st.session_state.resultados:
        st.error("Execute uma simulação antes de exportar os resultados.")
        return None

    if formato == "excel":
        output = BytesIO()
        # Adicionar código para gerar Excel
        return output.getvalue()
    elif formato == "pdf":
        output = BytesIO()
        # Adicionar código para gerar PDF
        return output.getvalue()

    return None


# Função para executar a simulação
def executar_simulacao(dados_empresa, ano_inicial, ano_final):
    """Executa a simulação com os dados fornecidos."""
    # Atualizar configurações do ICMS
    st.session_state.config.icms_config["aliquota_entrada"] = dados_empresa.get("aliquota_entrada", 19) / 100
    st.session_state.config.icms_config["aliquota_saida"] = dados_empresa.get("aliquota_saida", 19) / 100

    # Preparar dados para a simulação
    dados_simulacao = {
        "faturamento": dados_empresa.get("faturamento", 0),
        "custos_tributaveis": dados_empresa.get("custos_tributaveis", 0),
        "custos_simples": dados_empresa.get("custos_simples", 0),
        "creditos_anteriores": dados_empresa.get("creditos_anteriores", 0),
        "setor": dados_empresa.get("setor", "padrao"),
        "regime": dados_empresa.get("regime", "real"),
        "imposto_devido": 0  # Será calculado iterativamente
    }

    # Definir anos para simulação
    anos = list(range(ano_inicial, ano_final + 1))

    try:
        # Executar simulação
        resultados = st.session_state.calculadora_iva.calcular_comparativo(dados_simulacao, anos)
        st.session_state.resultados = resultados

        # Calcular alíquotas equivalentes
        carga_atual = dados_empresa.get("carga_atual", 25)
        aliquotas_equivalentes = {}

        for ano in anos:
            aliquotas_equivalentes[ano] = st.session_state.calculadora_iva.calcular_aliquotas_equivalentes(
                dados_simulacao, carga_atual, ano
            )

        st.session_state.aliquotas_equivalentes = aliquotas_equivalentes

        # Obter memória de cálculo
        st.session_state.memoria_calculo = st.session_state.calculadora_iva.memoria_calculo

        return True
    except Exception as e:
        st.error(f"Erro na simulação: {str(e)}")
        return False


# Inicializar sessão
inicializar_sessao()

# Sidebar para configurações e ações
st.sidebar.title("Simulador da Reforma Tributária")
st.sidebar.image(
    "https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2022/dezembro/reforma-tributaria/art-reforma-jpg/@@images/image.jpeg",
    use_column_width=True)
opcao_sidebar = st.sidebar.radio("Navegação", ["Simulação", "Configurações", "Memória de Cálculo", "Sobre"])

# Conteúdo principal
if opcao_sidebar == "Simulação":
    st.title("Simulação do IVA Dual (CBS/IBS)")

    # Dividir a tela em colunas
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Dados da Empresa")

        # Formulário para entrada de dados
        with st.form(key="form_dados_empresa"):
            faturamento = st.number_input("Faturamento Anual (R$)", min_value=0.0, value=1000000.0, step=10000.0,
                                          format="%.2f")
            custos = st.number_input("Custos Tributáveis (R$)", min_value=0.0, value=400000.0, step=10000.0,
                                     format="%.2f")
            custos_simples = st.number_input("Custos de Fornecedores do Simples (R$)", min_value=0.0, value=0.0,
                                             step=10000.0, format="%.2f")
            creditos_anteriores = st.number_input("Créditos Anteriores (R$)", min_value=0.0, value=0.0, step=10000.0,
                                                  format="%.2f")

            setor = st.selectbox("Setor de Atividade", list(st.session_state.config.setores_especiais.keys()))
            regime = st.selectbox("Regime Tributário", ["real", "presumido", "simples"])

            # Parâmetros de ICMS
            st.subheader("Parâmetros de ICMS")

            aliquota_entrada = st.number_input("Alíquota Média de Entrada (%)", min_value=0.0, max_value=100.0,
                                               value=19.0, step=0.1, format="%.2f")
            aliquota_saida = st.number_input("Alíquota Média de Saída (%)", min_value=0.0, max_value=100.0, value=19.0,
                                             step=0.1, format="%.2f")

            # Configurar período de simulação
            st.subheader("Período da Simulação")

            ano_inicial = st.selectbox("Ano Inicial", list(st.session_state.config.fase_transicao.keys()))
            ano_final = st.selectbox("Ano Final", list(st.session_state.config.fase_transicao.keys()),
                                     index=len(st.session_state.config.fase_transicao.keys()) - 1)

            # Carga tributária atual
            carga_atual = st.number_input("Carga Tributária Atual Estimada (%)", min_value=0.0, max_value=100.0,
                                          value=25.0, step=0.5, format="%.2f")

            # Botão para simular
            simular = st.form_submit_button("Simular")

        # Processar simulação se o botão for clicado
        if simular:
            dados_empresa = {
                "faturamento": faturamento,
                "custos_tributaveis": custos,
                "custos_simples": custos_simples,
                "creditos_anteriores": creditos_anteriores,
                "setor": setor,
                "regime": regime,
                "aliquota_entrada": aliquota_entrada,
                "aliquota_saida": aliquota_saida,
                "carga_atual": carga_atual
            }

            with st.spinner("Executando simulação..."):
                sucesso = executar_simulacao(dados_empresa, ano_inicial, ano_final)

                if sucesso:
                    st.success("Simulação concluída com sucesso!")

        # Incentivos fiscais (expander)
        with st.expander("Incentivos Fiscais de ICMS"):
            # Tabs para separar os tipos de incentivos
            tab_saida, tab_entrada, tab_apuracao = st.tabs(
                ["Incentivos de Saída", "Incentivos de Entrada", "Incentivos de Apuração"])

            # Incentivos de Saída
            with tab_saida:
                st.subheader("Incentivos de Saída")

                # Listar incentivos existentes
                if st.session_state.config.icms_config["incentivos_saida"]:
                    st.write("Incentivos configurados:")
                    for i, incentivo in enumerate(st.session_state.config.icms_config["incentivos_saida"]):
                        col_inc1, col_inc2, col_inc3 = st.columns([3, 1, 1])
                        with col_inc1:
                            st.write(f"{incentivo['descricao']} ({incentivo['tipo']})")
                        with col_inc2:
                            st.write(f"{formatar_br(incentivo['percentual'] * 100)}%")
                        with col_inc3:
                            if st.button(f"Remover#s{i}", key=f"remover_saida_{i}"):
                                remover_incentivo("saida", i)
                                st.rerun()

                # Formulário para adicionar novo incentivo
                with st.form(key="form_incentivo_saida"):
                    st.subheader("Adicionar Incentivo de Saída")

                    desc_saida = st.text_input("Descrição", value="", key="desc_saida")
                    tipo_saida = st.selectbox(
                        "Tipo",
                        ["Nenhum", "Redução de Alíquota", "Crédito Presumido/Outorgado", "Redução de Base de Cálculo",
                         "Diferimento"],
                        key="tipo_saida"
                    )
                    perc_saida = st.number_input("Percentual do Incentivo (%)", min_value=0.0, max_value=100.0,
                                                 value=0.0, step=1.0, key="perc_saida")
                    oper_saida = st.number_input("Percentual de Operações (%)", min_value=0.0, max_value=100.0,
                                                 value=100.0, step=1.0, key="oper_saida")
                    adicionar_saida = st.form_submit_button("Adicionar")

                if adicionar_saida:
                    dados_incentivo = {
                        "descricao": desc_saida or f"Incentivo Saída {len(st.session_state.config.icms_config['incentivos_saida']) + 1}",
                        "tipo": tipo_saida,
                        "percentual": perc_saida,
                        "perc_operacoes": oper_saida
                    }
                    if adicionar_incentivo("saida", dados_incentivo):
                        st.success("Incentivo de saída adicionado com sucesso!")
                        st.rerun()

            # Incentivos de Entrada
            with tab_entrada:
                st.subheader("Incentivos de Entrada")

                # Listar incentivos existentes
                if st.session_state.config.icms_config["incentivos_entrada"]:
                    st.write("Incentivos configurados:")
                    for i, incentivo in enumerate(st.session_state.config.icms_config["incentivos_entrada"]):
                        col_inc1, col_inc2, col_inc3 = st.columns([3, 1, 1])
                        with col_inc1:
                            st.write(f"{incentivo['descricao']} ({incentivo['tipo']})")
                        with col_inc2:
                            st.write(f"{formatar_br(incentivo['percentual'] * 100)}%")
                        with col_inc3:
                            if st.button(f"Remover#e{i}", key=f"remover_entrada_{i}"):
                                remover_incentivo("entrada", i)
                                st.rerun()

                # Formulário para adicionar novo incentivo
                with st.form(key="form_incentivo_entrada"):
                    st.subheader("Adicionar Incentivo de Entrada")

                    desc_entrada = st.text_input("Descrição", value="", key="desc_entrada")
                    tipo_entrada = st.selectbox(
                        "Tipo",
                        ["Nenhum", "Redução de Alíquota", "Crédito Presumido/Outorgado", "Redução de Base de Cálculo", "Estorno de Crédito"],
                        key="tipo_entrada"
                    )
                    perc_entrada = st.number_input("Percentual do Incentivo (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="perc_entrada")
                    oper_entrada = st.number_input("Percentual de Operações (%)", min_value=0.0, max_value=100.0, value=100.0, step=1.0, key="oper_entrada")

                    adicionar_entrada = st.form_submit_button("Adicionar")

                if adicionar_entrada:
                    dados_incentivo = {
                        "descricao": desc_entrada or f"Incentivo Entrada {len(st.session_state.config.icms_config['incentivos_entrada']) + 1}",
                        "tipo": tipo_entrada,
                        "percentual": perc_entrada,
                        "perc_operacoes": oper_entrada
                    }
                    if adicionar_incentivo("entrada", dados_incentivo):
                        st.success("Incentivo de entrada adicionado com sucesso!")
                        st.rerun()

            # Incentivos de Apuração
            with tab_apuracao:
                st.subheader("Incentivos de Apuração")

                # Listar incentivos existentes
                if st.session_state.config.icms_config["incentivos_apuracao"]:
                    st.write("Incentivos configurados:")
                    for i, incentivo in enumerate(st.session_state.config.icms_config["incentivos_apuracao"]):
                        col_inc1, col_inc2, col_inc3 = st.columns([3, 1, 1])
                        with col_inc1:
                            st.write(f"{incentivo['descricao']} ({incentivo['tipo']})")
                        with col_inc2:
                            st.write(f"{formatar_br(incentivo['percentual'] * 100)}%")
                        with col_inc3:
                            if st.button(f"Remover#a{i}", key=f"remover_apuracao_{i}"):
                                remover_incentivo("apuracao", i)
                                st.rerun()

                # Formulário para adicionar novo incentivo
                with st.form(key="form_incentivo_apuracao"):
                    st.subheader("Adicionar Incentivo de Apuração")

                    desc_apuracao = st.text_input("Descrição", value="", key="desc_apuracao")
                    tipo_apuracao = st.selectbox(
                        "Tipo",
                        ["Nenhum", "Crédito Presumido/Outorgado", "Redução do Saldo Devedor"],
                        key="tipo_apuracao"
                    )
                    perc_apuracao = st.number_input("Percentual do Incentivo (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="perc_apuracao")
                    oper_apuracao = st.number_input("Percentual do Saldo (%)", min_value=0.0, max_value=100.0, value=100.0, step=1.0, key="oper_apuracao")

                    adicionar_apuracao = st.form_submit_button("Adicionar")

                if adicionar_apuracao:
                    dados_incentivo = {
                        "descricao": desc_apuracao or f"Incentivo Apuração {len(st.session_state.config.icms_config['incentivos_apuracao']) + 1}",
                        "tipo": tipo_apuracao,
                        "percentual": perc_apuracao,
                        "perc_operacoes": oper_apuracao
                    }
                    if adicionar_incentivo("apuracao", dados_incentivo):
                        st.success("Incentivo de apuração adicionado com sucesso!")
                        st.rerun()

    # Coluna para exibição dos resultados
    with col2:
        if st.session_state.resultados:
            # Exibir tabela de resultados
            st.subheader("Resultados da Simulação")

            # Preparar dados para a tabela
            dados_tabela = []
            anos = sorted(st.session_state.resultados.keys())

            for ano in anos:
                resultado = st.session_state.resultados[ano]
                valor_atual = st.session_state.aliquotas_equivalentes[ano]["valor_atual"]
                diferenca = resultado["imposto_devido"] - valor_atual

                dados_tabela.append({
                    "Ano": ano,
                    "CBS (R$)": resultado["cbs"],
                    "IBS (R$)": resultado["ibs"],
                    "Subtotal IVA (R$)": resultado["imposto_bruto"],
                    "Créditos (R$)": resultado["creditos"],
                    "IVA Devido (R$)": resultado["imposto_devido"],
                    "Impostos Atuais (R$)": resultado["impostos_atuais"]["total"],
                    "Total (R$)": resultado["total_devido"],
                    "Alíquota Efetiva (%)": resultado["aliquota_efetiva"] * 100,
                    "Variação (R$)": diferenca
                })

            # Converter para DataFrame
            df_resultados = pd.DataFrame(dados_tabela)

            # Formatar valores
            cols_dinheiro = ["CBS (R$)", "IBS (R$)", "Subtotal IVA (R$)", "Créditos (R$)",
                            "IVA Devido (R$)", "Impostos Atuais (R$)", "Total (R$)", "Variação (R$)"]

            for col in cols_dinheiro:
                df_resultados[col] = df_resultados[col].apply(lambda x: f"R$ {formatar_br(x)}")

            df_resultados["Alíquota Efetiva (%)"] = df_resultados["Alíquota Efetiva (%)"].apply(lambda x: f"{formatar_br(x)}%")

            # Exibir tabela
            st.dataframe(df_resultados.set_index("Ano"), use_container_width=True)

            # Exibir gráficos
            st.subheader("Análise Gráfica")

            # Tabs para organizar os gráficos
            tab_comp, tab_aliq, tab_trans, tab_inc = st.tabs(["Composição Tributária", "Alíquota Efetiva", "Evolução na Transição", "Impacto dos Incentivos"])

            with tab_comp:
                grafico_comp = criar_grafico_comparativo(st.session_state.resultados, "Comparativo de Impostos por Ano")
                if grafico_comp:
                    st.plotly_chart(grafico_comp, use_container_width=True)

            with tab_aliq:
                grafico_aliq = criar_grafico_aliquotas(st.session_state.resultados, "Evolução da Alíquota Efetiva")
                if grafico_aliq:
                    st.plotly_chart(grafico_aliq, use_container_width=True)

            with tab_trans:
                grafico_trans = criar_grafico_transicao(st.session_state.resultados, "Evolução Tributária na Transição")
                if grafico_trans:
                    st.plotly_chart(grafico_trans, use_container_width=True)

            with tab_inc:
                grafico_inc = criar_grafico_incentivos(st.session_state.resultados, "Impacto dos Incentivos Fiscais no ICMS")
                if grafico_inc:
                    st.plotly_chart(grafico_inc, use_container_width=True)

            # Botões para exportar resultados
            st.subheader("Exportar Resultados")
            col_exp1, col_exp2 = st.columns(2)

            with col_exp1:
                if st.button("Exportar para Excel", key="bt_excel"):
                    # Implementar exportação para Excel
                    st.info("Funcionalidade de exportação para Excel em desenvolvimento.")

            with col_exp2:
                if st.button("Exportar para PDF", key="bt_pdf"):
                    # Implementar exportação para PDF
                    st.info("Funcionalidade de exportação para PDF em desenvolvimento.")

# Tab de Configurações
elif opcao_sidebar == "Configurações":
    st.title("Configurações do Simulador")

    # Subtabs para diferentes categorias de configuração
    tab1, tab2, tab3, tab4 = st.tabs(["Alíquotas Base", "Fases de Transição", "Setores", "Salvar/Carregar"])

    # Tab Alíquotas Base
    with tab1:
        st.subheader("Alíquotas Base do IVA Dual")
        st.info("Configure as alíquotas básicas do CBS e IBS conforme a LC 214/2025.")

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            cbs_aliq = st.number_input(
                "Alíquota CBS (%)",
                min_value=0.0,
                max_value=20.0,
                value=float(st.session_state.config.aliquotas_base["CBS"] * 100),
                step=0.1,
                format="%.2f",
                key="aliq_cbs"
            )

        with col_a2:
            ibs_aliq = st.number_input(
                "Alíquota IBS (%)",
                min_value=0.0,
                max_value=30.0,
                value=float(st.session_state.config.aliquotas_base["IBS"] * 100),
                step=0.1,
                format="%.2f",
                key="aliq_ibs"
            )

        if st.button("Atualizar Alíquotas Base", key="update_aliq"):
            st.session_state.config.aliquotas_base["CBS"] = cbs_aliq / 100
            st.session_state.config.aliquotas_base["IBS"] = ibs_aliq / 100
            st.success("Alíquotas base atualizadas com sucesso!")

    # Tab Fases de Transição
    with tab2:
        st.subheader("Fases de Transição do IVA Dual")
        st.info("Configure o percentual progressivo de implementação para cada ano (2026-2033).")

        # Criar uma lista para armazenar os valores atualizados
        valores_fases = {}

        # Criar colunas para exibir os inputs
        col1, col2, col3, col4 = st.columns(4)

        cols = [col1, col2, col3, col4]
        anos = sorted(list(st.session_state.config.fase_transicao.keys()))

        # Distribuir os anos entre as colunas
        for i, ano in enumerate(anos):
            col = cols[i % 4]
            with col:
                valor = st.number_input(
                    f"Ano {ano} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(st.session_state.config.fase_transicao[ano] * 100),
                    step=1.0,
                    format="%.1f",
                    key=f"fase_{ano}"
                )
                valores_fases[ano] = valor / 100

        if st.button("Atualizar Fases de Transição", key="update_fases"):
            for ano, valor in valores_fases.items():
                st.session_state.config.fase_transicao[ano] = valor
            st.success("Fases de transição atualizadas com sucesso!")

    # Tab Setores
    with tab3:
        st.subheader("Configurações por Setor")
        st.info("Configure as alíquotas específicas e reduções para cada setor.")

        # Criar uma tabela para edição
        setores_df = pd.DataFrame({
            "Setor": list(st.session_state.config.setores_especiais.keys()),
            "IBS (%)": [setor["IBS"] * 100 for setor in st.session_state.config.setores_especiais.values()],
            "Redução CBS (%)": [setor["reducao_CBS"] * 100 for setor in st.session_state.config.setores_especiais.values()]
        })

        edited_df = st.data_editor(
            setores_df,
            column_config={
                "Setor": st.column_config.TextColumn("Setor", disabled=True),
                "IBS (%)": st.column_config.NumberColumn("IBS (%)", min_value=0.0, max_value=30.0, step=0.1, format="%.2f"),
                "Redução CBS (%)": st.column_config.NumberColumn("Redução CBS (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f")
            },
            use_container_width=True,
            hide_index=True
        )

        if st.button("Atualizar Configurações Setoriais", key="update_setores"):
            # Atualizar as configurações com os valores editados
            for i, setor in enumerate(edited_df["Setor"]):
                st.session_state.config.setores_especiais[setor]["IBS"] = edited_df.iloc[i]["IBS (%)"] / 100
                st.session_state.config.setores_especiais[setor]["reducao_CBS"] = edited_df.iloc[i]["Redução CBS (%)"] / 100

            st.success("Configurações setoriais atualizadas com sucesso!")

    # Tab Salvar/Carregar
    with tab4:
        st.subheader("Salvar/Carregar Configurações")
        st.info("Salve suas configurações em um arquivo JSON ou carregue configurações salvas anteriormente.")

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            # Salvar configurações
            nome_arquivo = st.text_input("Nome do arquivo para salvar", "config_simulador.json")

            if st.button("Salvar Configurações", key="salvar_config"):
                try:
                    sucesso = st.session_state.config.salvar_configuracoes(nome_arquivo)
                    if sucesso:
                        st.success(f"Configurações salvas com sucesso em '{nome_arquivo}'!")
                    else:
                        st.error("Não foi possível salvar as configurações.")
                except Exception as e:
                    st.error(f"Erro ao salvar configurações: {str(e)}")

        with col_s2:
            # Carregar configurações
            uploaded_file = st.file_uploader("Carregar arquivo de configurações", type=["json"])

            if uploaded_file is not None:
                try:
                    # Salvar o arquivo temporariamente
                    with open("temp_config.json", "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Carregar configurações
                    sucesso = st.session_state.config.carregar_configuracoes("temp_config.json")

                    if sucesso:
                        # Atualizar a calculadora com as novas configurações
                        st.session_state.calculadora_iva = CalculadoraIVADual(st.session_state.config)
                        st.success("Configurações carregadas com sucesso!")
                    else:
                        st.error("Não foi possível carregar as configurações.")
                except Exception as e:
                    st.error(f"Erro ao carregar configurações: {str(e)}")

# Tab Memória de Cálculo
elif opcao_sidebar == "Memória de Cálculo":
    st.title("Memória de Cálculo")

    # Verificar se existem resultados
    if not st.session_state.resultados:
        st.warning("Execute uma simulação primeiro para visualizar a memória de cálculo.")
    else:
        # Selecionar ano para exibir memória de cálculo
        anos = sorted(list(st.session_state.resultados.keys()))
        ano_selecionado = st.selectbox("Selecione o ano para visualizar a memória de cálculo", anos)

        # Obter memória de cálculo
        memoria = st.session_state.memoria_calculo

        if memoria:
            # Exibir em seções expansíveis
            st.subheader(f"Memória de Cálculo - Ano {ano_selecionado}")

            # Validação de dados
            with st.expander("Validação de Dados", expanded=False):
                for linha in memoria.get("validacao", []):
                    st.write(linha)

            # Base tributável
            with st.expander("Base Tributável", expanded=False):
                for linha in memoria.get("base_tributavel", []):
                    st.write(linha)

            # Alíquotas
            with st.expander("Alíquotas", expanded=False):
                for linha in memoria.get("aliquotas", []):
                    st.write(linha)

            # CBS
            with st.expander("Cálculo da CBS", expanded=False):
                for linha in memoria.get("cbs", []):
                    st.write(linha)

            # IBS
            with st.expander("Cálculo do IBS", expanded=False):
                for linha in memoria.get("ibs", []):
                    st.write(linha)

            # Créditos
            with st.expander("Cálculo dos Créditos", expanded=False):
                for linha in memoria.get("creditos", []):
                    st.write(linha)

            # Imposto devido
            with st.expander("Cálculo do Imposto Devido", expanded=False):
                for linha in memoria.get("imposto_devido", []):
                    st.write(linha)

            # Impostos Atuais
            with st.expander("Cálculo dos Impostos Atuais", expanded=True):
                # PIS
                st.markdown("**PIS:**")
                for linha in memoria.get("impostos_atuais", {}).get("PIS", []):
                    st.write(linha)

                # COFINS
                st.markdown("**COFINS:**")
                for linha in memoria.get("impostos_atuais", {}).get("COFINS", []):
                    st.write(linha)

                # ICMS
                st.markdown("**ICMS:**")
                for linha in memoria.get("impostos_atuais", {}).get("ICMS", []):
                    st.write(linha)

                # ISS
                st.markdown("**ISS:**")
                for linha in memoria.get("impostos_atuais", {}).get("ISS", []):
                    st.write(linha)

                # IPI
                st.markdown("**IPI:**")
                for linha in memoria.get("impostos_atuais", {}).get("IPI", []):
                    st.write(linha)

                # Total Impostos Atuais
                st.markdown("**Total Impostos Atuais:**")
                for linha in memoria.get("impostos_atuais", {}).get("total", []):
                    st.write(linha)

            # Créditos Cruzados
            if memoria.get("creditos_cruzados"):
                with st.expander("Créditos Cruzados", expanded=False):
                    for linha in memoria.get("creditos_cruzados", []):
                        st.write(linha)

            # Total Devido
            with st.expander("Total Devido", expanded=False):
                for linha in memoria.get("total_devido", []):
                    st.write(linha)

            # Opção para exportar a memória de cálculo
            if st.button("Exportar Memória de Cálculo", key="export_memoria"):
                try:
                    # Criar uma string formatada com a memória de cálculo
                    texto_memoria = f"MEMÓRIA DE CÁLCULO - ANO {ano_selecionado}\n\n"

                    # Adicionar seções
                    texto_memoria += "=== VALIDAÇÃO DE DADOS ===\n"
                    for linha in memoria.get("validacao", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== BASE TRIBUTÁVEL ===\n"
                    for linha in memoria.get("base_tributavel", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== ALÍQUOTAS ===\n"
                    for linha in memoria.get("aliquotas", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== CÁLCULO DA CBS ===\n"
                    for linha in memoria.get("cbs", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== CÁLCULO DO IBS ===\n"
                    for linha in memoria.get("ibs", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== CÁLCULO DOS CRÉDITOS ===\n"
                    for linha in memoria.get("creditos", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== CÁLCULO DO IMPOSTO DEVIDO ===\n"
                    for linha in memoria.get("imposto_devido", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    texto_memoria += "=== CÁLCULO DOS IMPOSTOS ATUAIS ===\n"

                    texto_memoria += "\n--- PIS ---\n"
                    for linha in memoria.get("impostos_atuais", {}).get("PIS", []):
                        texto_memoria += f"{linha}\n"

                    texto_memoria += "\n--- COFINS ---\n"
                    for linha in memoria.get("impostos_atuais", {}).get("COFINS", []):
                        texto_memoria += f"{linha}\n"

                    texto_memoria += "\n--- ICMS ---\n"
                    for linha in memoria.get("impostos_atuais", {}).get("ICMS", []):
                        texto_memoria += f"{linha}\n"

                    texto_memoria += "\n--- ISS ---\n"
                    for linha in memoria.get("impostos_atuais", {}).get("ISS", []):
                        texto_memoria += f"{linha}\n"

                    texto_memoria += "\n--- IPI ---\n"
                    for linha in memoria.get("impostos_atuais", {}).get("IPI", []):
                        texto_memoria += f"{linha}\n"

                    texto_memoria += "\n--- TOTAL IMPOSTOS ATUAIS ---\n"
                    for linha in memoria.get("impostos_atuais", {}).get("total", []):
                        texto_memoria += f"{linha}\n"
                    texto_memoria += "\n"

                    if memoria.get("creditos_cruzados"):
                        texto_memoria += "=== CRÉDITOS CRUZADOS ===\n"
                        for linha in memoria.get("creditos_cruzados", []):
                            texto_memoria += f"{linha}\n"
                        texto_memoria += "\n"

                    texto_memoria += "=== TOTAL DEVIDO ===\n"
                    for linha in memoria.get("total_devido", []):
                        texto_memoria += f"{linha}\n"

                    # Gerar arquivo para download
                    b64 = base64.b64encode(texto_memoria.encode()).decode()
                    href = f'<a href="data:file/txt;base64,{b64}" download="memoria_calculo_{ano_selecionado}.txt">Baixar arquivo de memória de cálculo</a>'
                    st.markdown(href, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Erro ao exportar memória de cálculo: {str(e)}")

# Tab Sobre
elif opcao_sidebar == "Sobre":
    st.title("Sobre o Simulador de Reforma Tributária")

    # Logo e título
    col_logo, col_titulo = st.columns([1, 3])

    with col_logo:
        st.image("https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2022/dezembro/reforma-tributaria/art-reforma-jpg/@@images/image.jpeg", width=150)

    with col_titulo:
        st.markdown("""
        # Simulador do IVA Dual (CBS/IBS)
        ### Conforme a Lei Complementar 214/2025
        
        **Versão:** 1.0.0
        **Data:** 12/04/2025
        """)

    # Descrição
    st.markdown("""
    ## Sobre este Simulador
    
    Este simulador foi desenvolvido para auxiliar empresas e profissionais a compreender e planejar a transição para o novo sistema tributário brasileiro, baseado no IVA Dual (CBS/IBS), conforme estabelecido pela Lei Complementar 214/2025.
    
    O aplicativo permite simular a carga tributária durante o período de transição (2026-2033), considerando as particularidades setoriais, regimes tributários e incentivos fiscais.
    
    ## Principais Características
    
    - **Simulação Completa**: Cálculo detalhado do IVA Dual (CBS e IBS) e dos impostos do sistema atual durante a transição.
    - **Análise Setorial**: Consideração das alíquotas diferenciadas por setor de atividade.
    - **Incentivos Fiscais**: Simulação do impacto de diversos tipos de incentivos fiscais no ICMS.
    - **Créditos Cruzados**: Implementação das regras de aproveitamento de créditos entre o novo e o antigo sistema.
    - **Memória de Cálculo**: Detalhamento passo a passo de todos os cálculos realizados.
    - **Visualização Gráfica**: Gráficos interativos para melhor compreensão dos resultados.
    
    ## Base Legal
    
    - **Emenda Constitucional nº 132/2023**
    - **Lei Complementar nº 214/2025**
    - **Decretos Regulamentadores**
    - **Portarias e Instruções Normativas**
    
    ## Como Utilizar
    
    1. **Dados da Empresa**: Preencha as informações básicas da empresa e configure os parâmetros de ICMS.
    2. **Incentivos Fiscais**: Configure os incentivos fiscais aplicáveis, se houver.
    3. **Simulação**: Execute a simulação para o período desejado.
    4. **Análise**: Consulte os resultados na tabela e nos gráficos gerados.
    5. **Memória de Cálculo**: Verifique o detalhamento dos cálculos na aba específica.
    
    ## Limitações e Observações
    
    - Este simulador é uma ferramenta de apoio e seus resultados devem ser interpretados por profissionais qualificados.
    - As implementações seguem a legislação vigente até a data de desenvolvimento, podendo haver alterações posteriores.
    - Particularidades específicas de determinados setores ou operações podem requerer análises complementares.
    
    ## Suporte e Contato
    
    Para dúvidas, sugestões ou reportar problemas, entre em contato através do e-mail: suporte@expertzy.com.br
    
    ---
    
    © 2025 Expertzy Inteligência Tributária. Todos os direitos reservados.
    """)

    # Informações técnicas
    with st.expander("Informações Técnicas", expanded=False):
        st.markdown("""
        ### Detalhes Técnicos
        
        **Tecnologias Utilizadas:**
        - Python 3.9+
        - Streamlit 1.32.0+
        - Pandas, NumPy, Matplotlib
        - Plotly
        
        **Estrutura do Código:**
        - `app.py`: Aplicação principal (interface Streamlit)
        - `config.py`: Configurações tributárias
        - `calculadoras.py`: Classes de cálculo (CalculadoraTributosAtuais, CalculadoraIVADual)
        - `utils.py`: Funções utilitárias
        
        **Licença de Uso:**
        Este software é proprietário e sua distribuição, modificação ou uso comercial sem autorização é proibido.
        """)

# Rodapé
st.markdown("---")
st.markdown("© 2025 Expertzy Inteligência Tributária. Todos os direitos reservados.")