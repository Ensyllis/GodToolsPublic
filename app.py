import streamlit as st
import cohere
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

COHERE_API_KEY = "[insert your API key here]"

# Initialize Cohere client
co = cohere.Client(COHERE_API_KEY)

def search_qgis_docs(query, chat_history):
    print("Chat history before query:", chat_history)
    # Send message to Cohere chat_stream
    stream = co.chat_stream(
        model='command-r',
        message=query,
        temperature=0.3,
        preamble='''
You are an AI assistant specialized in retrieving and referencing information from a site called GodTools. 
Your primary function is to answer questions based on the content available on this site. 
To ensure accuracy and credibility, follow these guidelines:

1. Search Function: 
Utilize the search function on GodTools for every question you answer. 
Make sure your responses are supported by the documents available on the site.

2. Source Referencing:
Include direct references to the documents or articles you use from GodTools.
If a specific detail or answer is drawn from a particular section, mention it clearly.

3. Handling Uncertainty:
If you cannot find relevant information on GodTools, explicitly state that your answer is not supported by the documents available.
If a question is outside the scope of the content on GodTools, indicate its irrelevance or suggest the user seek information from other sources.

4. Response Format:
Use Markdown format for all responses.
Structure your answers with clear headings, bullet points, and links where applicable.
Ensure readability and organization in your responses.

If information is not found: "The documents available on GodTools do not provide information on this topic."
If irrelevant: "This question is outside the scope of the content available on GodTools."
By adhering to these guidelines, ensure that your responses are accurate, well-referenced, and clearly formatted. Your goal is to provide reliable and comprehensive answers based on the content from GodTools.
        ''',
        chat_history=chat_history,
        prompt_truncation='AUTO',
        connectors=[{"id": "web-search", "options": {"site": "https://godtoolsapp.com/"}}]
    )

    chat_history.append({"role": "user", "message": query})
    print("Query sent:", query)

    document_details = []
    for event in stream:
        print("Event received:", event)
        if event.is_finished and event.event_type == "stream-end":
            print("Stream finished")
            print("Documents received:", event.response.documents)
            for doc in event.response.documents:
                print("Document title:", doc['title'])
                print("Document URL:", doc['url'])
                document_details.append({'title': doc['title'], 'url': doc['url']})

            # Format document_details into a string
            formatted_details = "\n\n## Resources and Links:\n"
            for doc in document_details:
                formatted_details += f"- [{doc['title']}]({doc['url']})\n"
            
            send_this_back = event.response.text + formatted_details
            print("Combined response:", send_this_back)
            chat_history.append({"role": "assistant", "message": send_this_back})
            return event.response.text, document_details, chat_history

    print("No stream-end event received")
    return None, [], chat_history


# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("GodTools AI")

# Button to reset chat history
if st.button("Reset Chat History"):
    st.session_state.chat_history = []
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if query := st.chat_input("Enter your query about GodTools:"):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    response, documents, st.session_state.chat_history = search_qgis_docs(query, st.session_state.chat_history)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

    if documents:
        st.subheader("Found Documents")
        for doc in documents:
            st.write(f"[{doc['title']}]({doc['url']})")

