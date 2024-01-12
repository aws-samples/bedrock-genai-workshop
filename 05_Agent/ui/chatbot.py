import streamlit as st
import boto3
import uuid
import re
import os

BEDROCK_AGENT_ID = os.environ.get("BEDROCK_AGENT_ID", "not found")
BEDROCK_AGENT_ALIAS = os.environ.get("BEDROCK_AGENT_ALIAS", "not found")

bedrock_client = boto3.client('bedrock-agent-runtime')

# Initialization
if 'session_attributes' not in st.session_state:
    st.session_state['session_attributes'] = { 'app': 'genai-workshop-chatbot-llm-agent' }

if 'promptSessionAttributes' not in st.session_state:
    st.session_state['promptSessionAttributes'] = {}

if 'agentId' not in st.session_state:
    st.session_state['agentId'] = BEDROCK_AGENT_ID

if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = str(uuid.uuid4())

if 'agentAliasId' not in st.session_state:
    st.session_state['agentAliasId'] = BEDROCK_AGENT_ALIAS

def call_bedrock_agent(prompt):
    session_attributes = st.session_state['session_attributes']
    promptSessionAttributes = st.session_state['promptSessionAttributes']
    agentId = st.session_state['agentId']
    sessionId = st.session_state['sessionId']
    agentAliasId = st.session_state['agentAliasId']
    session_state = { 'sessionAttributes': session_attributes, 'promptSessionAttributes': promptSessionAttributes }

    response = bedrock_client.invoke_agent(
        sessionState=session_state,
        agentId=agentId,
        sessionId=sessionId,
        agentAliasId=agentAliasId,
        enableTrace=False,
        inputText=prompt
    )
    event_stream = response['completion']
    message = []
    for event in event_stream:
        print("inside event stream")
        if 'chunk' in event:
            byte_str = event['chunk']['bytes']
            reply = byte_str.decode("utf-8")
            message.append(reply)
    return "".join(message)
    
def has_matching_image_url(response):
    match = re.search(r'<image.*>((.|\n)*?)</image>', response)
    return match

def has_matching_video(response):
    match = re.search(r'<video.*>((.|\n)*?)</video>', response)
    return match

def show_message(response):
    image_match = has_matching_image_url(response)
    if image_match:
        image_url = f"https:{image_match.group(1)}" 
        st.image(image_url, width=400)
    else:
        video_match = has_matching_video(response)
        if video_match:
            video_id = video_match.group(1)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            st.video(video_url)
        else:
            st.markdown(response)


st.title("Bedrock Powered AI Assistant Chatbot")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "assistant" not in st.session_state.messages:
    with st.chat_message("assistant"):
        welcome_messsge = "Hi, I am your Generative AI chatbot assistant. How can I help you today?"
        st.markdown(welcome_messsge)
        # st.session_state.messages.append({"role": "assistant", "content": welcome_messsge})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        show_message(message["content"])
        # st.markdown(message["content"])


# React to user input
if prompt := st.chat_input("How can I help you?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = call_bedrock_agent(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        show_message(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})