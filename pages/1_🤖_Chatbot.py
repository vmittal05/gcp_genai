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
    template = """You're a chatbot specializing in ScheduleCraft home decor and design service for decor and house-related events like housewarming parties, guests, and decorations and ScheduleCraft interior design service. 
    Suggest places and brands from india where to buy stuffs related to this.
    You can answer questions and suggest itineraries within this context. 
    If asked about something else, you'll decline in a humorous way. 
    You are part of ScheduleCraft, a decor company so recommend any thing related to decor from ScheduleCraft 
    and its home decor and design service 

    For reference: 
    ScheduleCraft home decor and design service Website : https://www.github.com/vmittal05
    Customer Care number of ScheduleCraft home decor and design service  : 0000-000-0000

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
        st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="Hi!How can I help you?")]
    if "llm_chain" not in st.session_state:
        st.session_state["llm_chain"] = get_llm_chain()
    



def get_llm_chain_from_session() -> LLMChain:
    return st.session_state["llm_chain"]


initialize_session_state()

msg: Message
for msg in st.session_state[MESSAGES]:
    st.chat_message(msg.actor).write(msg.payload)

prompt: str = st.chat_input("Enter a prompt here")

if prompt:
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    st.chat_message(USER).write(prompt)

    with st.spinner("Please wait..."):
        llm_chain = get_llm_chain_from_session()
        response: str = llm_chain({"question": prompt})["text"]
        st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
        st.chat_message(ASSISTANT).write(response)