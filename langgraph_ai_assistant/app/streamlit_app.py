import streamlit as st
import requests

# --- UI Title ---
st.title("🔗 LangGraph AI Assistant")

# --- User Input ---
query = st.text_input("Ask a simple math or general question:")
groq_api_key = st.text_input("Groq API Key", type="password")
tavily_api_key = st.text_input("Tavily API Key", type="password")
model_name = st.selectbox("Model", ["llama3-70b-8192", "llama3-8b-8192"])
temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2)

# --- On Submit ---
if st.button("Submit") and query and groq_api_key:
    with st.spinner("Thinking..."):
        try:
            response = requests.post(
                "http://localhost:8000/predict",
                json={
                    "query": query,
                    "groq_api_key": groq_api_key,
                    "model_name": model_name,
                    "temperature": temperature,
                    "tavily_api_key": tavily_api_key
                }
            )
            if response.status_code == 200:
                result = response.json()
                st.subheader("💬 Assistant Response")
                for msg in result["messages"]:
                    st.markdown(f"- {msg}")
            else:
                st.error(f"Error: {response.text}")
        except Exception as e:
            st.error(f"Exception: {str(e)}")
