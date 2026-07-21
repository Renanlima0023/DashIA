import streamlit as st
import pandas as pd
import plotly.express as px
import json
from google import genai
from google.genai import types

# Título da aplicação
st.set_page_config(page_title="Assistente de Dashboards", layout="wide")
st.title("📊 Criador Conversacional de Dashboards")
st.write("Envie sua planilha, converse sobre o estilo desejado e veja o gráfico ser gerado!")

# 1. Pega a chave da API salva nos Secrets do Streamlit automaticamente
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("⚠️ Chave de API não encontrada nos Secrets do Streamlit. Configure a variável GEMINI_API_KEY.")
    st.stop()

# 2. Upload da Planilha
uploaded_file = st.sidebar.file_uploader("1. Envie sua planilha (.csv ou .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    # Leitura dos dados
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.write("### 🔍 Prévia dos seus Dados")
    st.dataframe(df.head(3))

    # Extrai informações das colunas
    colunas_e_tipos = {col: str(df[col].dtype) for col in df.columns}
    exemplo_linhas = df.head(2).to_dict(orient="records")

    st.markdown("---")
    st.subheader("💬 Converse para gerar seu gráfico")

    # Campo para o usuário digitar o que quer
    prompt = st.text_input("O que você deseja analisar? (Ex: 'Crie um gráfico de barras com vendas por produto na cor azul')")

    if st.button("Gerar Gráfico"):
        if prompt:
            system_prompt = f"""
            Você é um assistente de visualização de dados.
            Colunas disponíveis: {json.dumps(colunas_e_tipos)}
            Amostra dos dados: {json.dumps(exemplo_linhas)}

            Responda APENAS um objeto JSON válido no seguinte formato (sem formatação markdown em volta):
            {{
                "explicacao": "Uma breve explicação do gráfico gerado.",
                "tipo_grafico": "bar" ou "line" ou "pie" ou "scatter",
                "x": "nome_da_coluna_eixo_x",
                "y": "nome_da_coluna_eixo_y",
                "titulo": "Título do Gráfico",
                "cor": "#1f77b4"
            }}
            """

            with st.spinner("A IA está analisando os dados e criando a visualização..."):
                try:
                    # Chamada ao Gemini
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[system_prompt, f"Pedido: {prompt}"],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    
                    config = json.loads(response.text)
                    st.success(config.get("explicacao"))

                    tipo = config.get("tipo_grafico")
                    x_col = config.get("x")
                    y_col = config.get("y")
                    titulo = config.get("titulo", "Dashboard")
                    cor = config.get("cor", "#1f77b4")

                    # Gerar gráfico Plotly
                    if tipo == "bar":
                        fig = px.bar(df, x=x_col, y=y_col, title=titulo, color_discrete_sequence=[cor])
                    elif tipo == "line":
                        fig = px.line(df, x=x_col, y=y_col, title=titulo, color_discrete_sequence=[cor])
                    elif tipo == "pie":
                        fig = px.pie(df, names=x_col, values=y_col, title=titulo)
                    else:
                        fig = px.scatter(df, x=x_col, y=y_col, title=titulo, color_discrete_sequence=[cor])

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
