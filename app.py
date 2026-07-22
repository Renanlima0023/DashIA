import streamlit as st
import pandas as pd
from groq import Groq

# Configuração da página do Streamlit
st.set_page_config(page_title="Criador Conversacional de Dashboards", layout="wide")

st.title("📊 Criador Conversacional de Dashboards (Estilo Power BI)")
st.write("Envie sua planilha, peça o gráfico desejado e exporte suas visualizações!")

# 1. Autenticação e Configuração do Cliente Groq
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("⚠️ Chave de API não encontrada nos Secrets do Streamlit. Configure a variável GROQ_API_KEY.")
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
        
        # Exibição e exportação da tabela original
        col_view, col_down = st.columns([3, 1])
        with col_view:
            with st.expander("👀 Dar uma olhada nos dados"):
                st.dataframe(df.head())
        with col_down:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Dados (CSV)",
                data=csv_data,
                file_name="dados_carregados.csv",
                mime="text/csv",
            )

        # Entrada de prompt do usuário
        user_prompt = st.text_input("Como você gostaria de visualizar estes dados? (Ex: Crie um gráfico de barras com as vendas por categoria)")

        if st.button("Gerar Dashboard / Gráfico"):
            if not user_prompt:
                st.warning("Por favor, digite o que você deseja visualizar.")
            else:
                with st.spinner("A IA está formatando o gráfico no estilo Power BI..."):
                    try:
                        amostra_dados = df.head(5).to_json(orient='records', date_format='iso')
                        colunas = list(df.columns)

                        # Instruções aprimoradas para visual profissional estilo Power BI
                        system_instruction = f"""
                        Você é um especialista em Business Intelligence (BI), Plotly e Streamlit.
                        O usuário forneceu um dataset com as seguintes colunas: {colunas}.
                        Amostra dos dados em JSON: {amostra_dados}

                        Sua tarefa é gerar APENAS o código Python necessário usando Streamlit e Plotly para exibir o gráfico solicitado pelo usuário.

                        REGRAS DE ESTILIZAÇÃO ESTILO POWER BI:
                        - Use o DataFrame chamado 'df'.
                        - Sempre configure o gráfico com o template profissional 'plotly_white' ou 'plotly_dark' (ex: fig.update_layout(template='plotly_white')).
                        - Adicione rótulos de dados (text_auto=True em plotly express ou update_traces(texttemplate=...)) para que os valores fiquem visíveis sobre as barras/linhas como no Power BI.
                        - Adicione um título claro e estilizado ao gráfico.
                        - Use cores modernas e limpas (ex: cores hexadecimais como #1f77b4, #2ca02c, #ff7f0e).
                        - Use `st.plotly_chart(fig, use_container_width=True)` para renderizar o gráfico responsivo.
                        - Retorne APENAS o código Python puro, sem marcadores como ```python ou explicações.
                        """

                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.2,
                        )

                        codigo_gerado = response.choices[0].message.content.strip()

                        # Limpeza do código retornado
                        if codigo_gerado.startswith("```python"):
                            codigo_gerado = codigo_gerado[9:]
                        if codigo_gerado.startswith("```"):
                            codigo_gerado = codigo_gerado[3:]
                        if codigo_gerado.endswith("```"):
                            codigo_gerado = codigo_gerado[:-3]

                        st.markdown("### 📈 Visualização Gerada")
                        
                        # Execução do código gerado
                        try:
                            import plotly.express as px
                            import plotly.graph_objects as go
                            
                            local_scope = {"df": df, "st": st, "px": px, "go": go, "pd": pd}
                            exec(codigo_gerado, local_scope)
                            
                            with st.expander("🛠️ Ver código Python gerado"):
                                st.code(codigo_gerado, language="python")

                        except Exception as e:
                            st.error(f"Erro ao desenhar o gráfico: {e}")
                            st.code(codigo_gerado, language="python")

                    except Exception as e:
                        st.error(f"Erro na comunicação com a API: {e}")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
