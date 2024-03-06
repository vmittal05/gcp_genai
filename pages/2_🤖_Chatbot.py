from dataclasses import dataclass

import streamlit as st
from langchain.chains import LLMChain
from langchain.llms import VertexAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from google.cloud import aiplatform
from google.cloud import bigquery
import vertexai

PROJECT_ID = "dark-caldron-414803"  
LOCATION = "us-central1"

aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)


st.set_page_config(
    page_title="Chatbot" ,
    page_icon="🤖",
)

@dataclass
class Message:
    actor: str
    payload: str


@st.cache_resource(show_spinner=False)
def get_llm() -> VertexAI:
    return VertexAI(model_name="gemini-pro",max_output_tokens=1024,temperature=0.5,top_p=1.0)


def get_llm_chain():
    template = """You're a chatbot specializing in Asian Paints beautiful home service for anything related to decor and house-related event plannings. 
    You answer the questions and suggest itineraries related to questions. 
    If asked about something else than event planning or home decor, you'll decline in a humorous way. 

    Reference:
    Asian paints Website: https://www.beautifulhomes.com/
    Asian Paints Customer care: 1800-209-5678

    Previous conversation:
    {chat_history}

    New human question: {question}
    Response:"""
    prompt_template = PromptTemplate.from_template(template)
    # Notice that we need to align the `memory_key`
    memory = ConversationBufferMemory(memory_key="chat_history")
    conversation = LLMChain(
        llm=get_llm(),
        prompt=prompt_template,
        verbose=True,
        memory=memory,

    )
    return conversation


USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"


def initialize_session_state():
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="I'm the Asian Paints Beautiful Homes Services chatbot, here to help with everything from decor dilemmas to event planning and, of course, all things Asian Paints!  What can I help you with today?")]
    if "llm_chain" not in st.session_state:
        st.session_state["llm_chain"] = get_llm_chain()
    



def get_llm_chain_from_session() -> LLMChain:
    return st.session_state["llm_chain"]


initialize_session_state()

msg: Message
for msg in st.session_state[MESSAGES]:
    st.chat_message(msg.actor).write(msg.payload)

prompt: str = st.chat_input("What's on your mind today?")

if prompt:
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    st.chat_message(USER).write(prompt)

    with st.spinner("Please wait..."):
        llm_chain = get_llm_chain_from_session()
        response: str = llm_chain({"question": prompt})["text"]
        st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
        st.chat_message(ASSISTANT).write(response)