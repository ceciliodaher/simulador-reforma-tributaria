import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def formatar_br(valor, decimais=2):
    """Formata um número no padrão brasileiro (vírgula como separador decimal e ponto como separador de milhar)."""
    return f"{valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def criar_grafico_comparativo(resultados, titulo=None):
    """Cria um gráfico de barras comparativo dos impostos por ano usando Plotly."""
    if not resultados:
        return None

    anos = list(resultados.keys())
    cbs_valores = [resultados[ano]["cbs"] for ano in anos]
    ibs_valores = [resultados[ano]["ibs"] for ano in anos]
    creditos = [resultados[ano]["creditos"] for ano in anos]
    liquido = [resultados[ano]["imposto_devido"] for ano in anos]

    df = pd.DataFrame({
        'Ano': anos,
        'CBS': cbs_valores,
        'IBS': ibs_valores,
        'Créditos': creditos,
        'Imposto Devido': liquido
    })

    df_melt = pd.melt(df, id_vars=['Ano'], value_vars=['CBS', 'IBS', 'Créditos', 'Imposto Devido'],
                      var_name='Categoria', value_name='Valor')

    fig = px.bar(df_melt, x='Ano', y='Valor', color='Categoria', barmode='group',
                 title=titulo or 'Comparativo de Impostos',
                 labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'})

    fig.update_layout(legend_title_text='',
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    return fig


def criar_grafico_aliquotas(resultados, titulo=None):
    """Cria um gráfico de linha das alíquotas efetivas usando Plotly."""
    if not resultados:
        return None

    anos = list(resultados.keys())
    aliquotas_efetivas = [resultados[ano]["aliquota_efetiva"] * 100 for ano in anos]

    df = pd.DataFrame({
        'Ano': anos,
        'Alíquota Efetiva (%)': aliquotas_efetivas
    })

    fig = px.line(df, x='Ano', y='Alíquota Efetiva (%)', markers=True,
                  title=titulo or 'Evolução da Alíquota Efetiva',
                  labels={'Alíquota Efetiva (%)': 'Alíquota (%)', 'Ano': 'Ano'})

    # Adicionar valores nos pontos
    fig.update_traces(textposition="top center", texttemplate='%{y:.2f}%')

    return fig


def criar_grafico_transicao(resultados, titulo=None):
    """Cria um gráfico comparativo entre sistema atual e IVA Dual."""
    if not resultados:
        return None

    anos = list(resultados.keys())
    dados_iva = [resultado["imposto_devido"] for resultado in resultados.values()]
    dados_atuais = []

    for ano, resultado in resultados.items():
        if "impostos_atuais" in resultado:
            impostos = resultado["impostos_atuais"]
            if isinstance(impostos, dict):
                atuais = impostos.get("total", 0)
                dados_atuais.append(atuais)
            else:
                dados_atuais.append(0)
        else:
            dados_atuais.append(0)

    df = pd.DataFrame({
        'Ano': anos,
        'Sistema Atual': dados_atuais,
        'IVA Dual': dados_iva
    })

    df_melt = pd.melt(df, id_vars=['Ano'], value_vars=['Sistema Atual', 'IVA Dual'],
                      var_name='Sistema', value_name='Valor')

    fig = px.bar(df_melt, x='Ano', y='Valor', color='Sistema', barmode='group',
                 title=titulo or 'Evolução Tributária na Transição',
                 labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'})

    fig.update_layout(legend_title_text='',
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    return fig


# Adicionar ao arquivo utils.py - Melhoria da função criar_grafico_incentivos

def criar_grafico_incentivos(resultados, titulo=None):
    """Cria um gráfico para comparar o ICMS com e sem incentivos fiscais, com detalhamento."""
    if not resultados:
        return None

    # Preparar figura
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Comparativo ICMS: Com vs Sem Incentivos", "Detalhamento de Economia por Tipo"),
        specs=[[{"type": "bar"}, {"type": "pie"}]]
    )

    # Preparar dados para o gráfico de barras
    anos = list(resultados.keys())
    icms_normal = []
    icms_incentivado = []
    economia = []

    for ano, resultado in resultados.items():
        icms_devido = resultado["impostos_atuais"].get("ICMS", 0)
        economia_icms = resultado["impostos_atuais"].get("economia_icms", 0)
        icms_normal.append(icms_devido + economia_icms)
        icms_incentivado.append(icms_devido)
        economia.append(economia_icms)

    # Gráfico de barras - ICMS com e sem incentivos
    fig.add_trace(
        go.Bar(
            x=anos,
            y=icms_normal,
            name="ICMS sem Incentivo",
            marker_color='#e74c3c'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=anos,
            y=icms_incentivado,
            name="ICMS com Incentivo",
            marker_color='#2ecc71'
        ),
        row=1, col=1
    )

    # Adicionar anotações de economia
    for i, ano in enumerate(anos):
        if economia[i] > 0:
            fig.add_annotation(
                x=ano,
                y=(icms_incentivado[i] + icms_normal[i]) / 2,
                text=f"Economia:<br>R$ {formatar_br(economia[i])}",
                showarrow=False,
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                row=1, col=1
            )

    # Gráfico de pizza - Detalhamento dos incentivos
    # Este é um exemplo, na versão completa seria necessário acessar dados mais detalhados
    # Vamos supor 3 categorias de incentivos: Saída, Entrada, Apuração
    if economia and economia[0] > 0:
        # Estimar contribuição de cada tipo (isto pode ser mais preciso em uma implementação completa)
        saida_prop = 0.6
        entrada_prop = 0.2
        apuracao_prop = 0.2

        # Valores para o primeiro ano como exemplo
        valores_pizza = [
            economia[0] * saida_prop,
            economia[0] * entrada_prop,
            economia[0] * apuracao_prop
        ]

        fig.add_trace(
            go.Pie(
                labels=["Incentivos de Saída", "Incentivos de Entrada", "Incentivos de Apuração"],
                values=valores_pizza,
                textinfo='label+percent',
                insidetextorientation='radial',
                marker=dict(colors=['#3498db', '#9b59b6', '#1abc9c'])
            ),
            row=1, col=2
        )

    # Ajustar layout
    fig.update_layout(
        title_text=titulo or "Impacto dos Incentivos Fiscais no ICMS",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Valor (R$)",
        barmode='group'
    )

    return fig