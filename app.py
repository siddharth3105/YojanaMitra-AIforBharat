import streamlit as st
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io

load_dotenv()

st.set_page_config(
    page_title="YojanaMitra - योजना मित्र",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; color: #FF9900; text-align: center;}
.sub-header {font-size: 1.2rem; color: #666; text-align: center;}
.scheme-card {background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #FF9900;}
.agent-badge {background-color: #FF9900; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.85rem;}
</style>
""", unsafe_allow_html=True)

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
REGION = os.getenv("AWS_REGION", "ap-south-1")

@st.cache_resource
def init_bedrock():
    return ChatBedrock(
        model_id=MODEL_ID,
        region_name=REGION,
        model_kwargs={"temperature": 0.1, "max_tokens": 2000},
        streaming=True
    )

llm = init_bedrock()

eligibility_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an eligibility agent for Indian government schemes."),
    ("human", "{user_input}")
])

chain_eligibility = eligibility_prompt | llm | StrOutputParser()

def generate_scheme_pdf(scheme_name, user_name, user_details, eligibility_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1*inch, height - 1*inch, "YojanaMitra - योजना मित्र")
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.4*inch, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.save()
    buffer.seek(0)
    return buffer

st.markdown('<div class="main-header">🏛️ YojanaMitra</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">आपकी सरकारी योजनाओं का AI साथी</div>', unsafe_allow_html=True)

user_name = st.text_input("नाम | Name")
user_input = st.text_area("अपने बारे में बताएं", height=150)

if st.button("🔍 योजना खोजें"):
    if user_input:
        with st.spinner("AI काम कर रहा है..."):
            result = chain_eligibility.invoke({"user_input": user_input})
            st.markdown(result)
    else:
        st.error("कृपया अपनी जानकारी दें।")
