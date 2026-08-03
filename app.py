import streamlit as st
from guardrails import check_guardrails
from retriever import RAGPipeline

# Page configuration
st.set_page_config(
    page_title="Groww Mutual Funds FAQ",
    page_icon="📈",
    layout="centered"
)

# Initialize RAG Pipeline only once
@st.cache_resource
def get_rag_pipeline():
    return RAGPipeline()

# Load the backend
rag = get_rag_pipeline()

# Title and Disclaimer
st.title("Groww Mutual Funds Assistant")
st.markdown("**_Facts-only. No investment advice._**")
st.divider()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # Add welcome message
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hi! I am an AI assistant specialized in Groww Mutual Funds. I can provide factual data like NAVs, expense ratios, and fund managers. How can I help you today?"
    })

# Sidebar with Example Questions
st.sidebar.header("Try these examples:")
examples = [
    "What is the expense ratio of Navi Nifty 50 Index Fund?",
    "Who is the CEO of Navi AMC?",
    "What is the exit load for Bajaj Finserv Flexi Cap Fund?"
]

for example in examples:
    if st.sidebar.button(example):
        st.session_state.example_query = example

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
# Either from the chat input or the sidebar example buttons
user_query = st.chat_input("Ask a factual question about a mutual fund...")
if "example_query" in st.session_state:
    user_query = st.session_state.example_query
    del st.session_state.example_query

if user_query:
    # 1. Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_query)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Step A: Guardrails Check
        with st.spinner("Checking compliance..."):
            guardrail_result = check_guardrails(user_query)
        
        if not guardrail_result["is_safe"]:
            # Display refusal message
            full_response = guardrail_result["message"]
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            # Step B: RAG Pipeline
            with st.spinner("Searching facts..."):
                rag_result = rag.generate_answer(user_query)
                
            # Construct final response
            full_response = rag_result["answer"]
            
            if rag_result.get("citation"):
                full_response += f"\n\n**Source:** [{rag_result['citation']}]({rag_result['citation']})"
                
            if rag_result.get("footer"):
                full_response += f"\n\n_{rag_result['footer']}_"
                
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
