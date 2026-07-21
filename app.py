import streamlit as st
import pandas as pd
from google import genai
from google.genai import types

# Configuração da página do Streamlit
st.set_page_config(page_title="Criador Conversacional de Dashboards", layout="wide")

st.title("📊 Criador Conversacional de Dashboards")
st.write("Envie sua planilha, converse sobre o estilo desejado e veja o gráfico ser gerado!")

# 1. Autenticação e Configuração do Cliente Gemini
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("⚠️ Chave de API não encontrada nos Secrets do Streamlit. Configure a variável GEMINI_API_KEY.")
    st.stop()

# 2. Upload da Planilha
uploaded_file = st.file_uploader("Escolha um arquivo CSV ou Excel", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("Planilha carregada com sucesso!")
        
        with st.expander("👀 Dar uma olhada nos dados"):
            st.dataframe(df.head())

        # Entrada de prompt do usuário
        user_prompt = st.text_input("Como você gostaria de visualizar estes dados? (Ex: Crie um gráfico de barras com as vendas por categoria)")

        if st.button("Gerar Dashboard / Gráfico"):
            if not user_prompt:
                st.warning("Por favor, digite o que você deseja visualizar.")
            else:
                with st.spinner("O Gemini está analisando seus dados e gerando o código do gráfico..."):
                    
                    # Converte os dados de amostra de forma segura sem quebrar o JSON
                    amostra_dados = df.head(5).to_json(orient='records', date_format='iso')
                    colunas = list(df.columns)

                    system_instruction = f"""
                    Você é um especialista em análise de dados e Python/Streamlit.
                    O usuário forneceu um dataset com as seguintes colunas: {colunas}.
                    Amostra dos dados em JSON: {amostra_dados}

                    Sua tarefa é gerar APENAS o código Python necessário usando Streamlit e Plotly para exibir o gráfico solicitado pelo usuário.
                    - Use o DataFrame chamado 'df'.
                    - Retorne APENAS o código Python sem marcadores de markdown adicionais ou explicações.
                    - Use `st.plotly_chart(fig)` para renderizar o gráfico no Streamlit.
                    """

                    # Chamada oficial da nova SDK do Gemini
                   response = client.models.generate_content(
    model='gemini-1.5-flash',
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2,
                        )
                    )

                    # Limpeza do código retornado
                    codigo_gerado = response.text.strip()
                    if codigo_gerado.startswith("```python"):
                        codigo_gerado = codigo_gerado[9:]
                    if codigo_gerado.startswith("```"):
                        codigo_gerado = codigo_gerado[3:]
                    if codigo_gerado.endswith("```"):
                        codigo_gerado = codigo_gerado[:-3]

                    st.markdown("### 📈 Visualização Gerada")
                    
                    # Execução segura do código gerado para exibir o gráfico no Streamlit
                    try:
                        import plotly.express as px
                        import plotly.graph_objects as go
                        
                        local_scope = {"df": df, "st": st, "px": px, "go": go}
                        exec(codigo_gerado, local_scope)
                    except Exception as e:
                        st.error(f"Erro ao desenhar o gráfico: {e}")
                        st.code(codigo_gerado, language="python")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
