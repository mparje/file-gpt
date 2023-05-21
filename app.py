import streamlit as st
from streamlit_chat import message
from utils import (
    parse_docx,
    parse_pdf,
    parse_txt,
    parse_csv,
    search_docs,
    embed_docs,
    text_to_docs,
    get_answer,
    parse_any,
    get_sources,
    wrap_text_in_html,
)
from openai.error import OpenAIError

def clear_submit():
    st.session_state["submit"] = False

def set_openai_api_key(api_key: str):
    st.session_state["OPENAI_API_KEY"] = api_key

# Sidebar
index = None
doc = None
user_secret = st.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="Paste your OpenAI API key here (sk-...)",
    help="You can get your API key from https://platform.openai.com/account/api-keys.",
    value=st.session_state.get("OPENAI_API_KEY", ""),
)
if user_secret:
    set_openai_api_key(user_secret)

uploaded_file = st.file_uploader(
    "Upload a pdf, docx, or txt file",
    type=["pdf", "docx", "txt", "csv", "js", "py", "json", "html", "css", "md"],
    help="Scanned documents are not supported yet!",
    on_change=clear_submit,
)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".pdf"):
        doc = parse_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        doc = parse_docx(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        doc = parse_csv(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        doc = parse_txt(uploaded_file)
    else:
        doc = parse_any(uploaded_file)
    text = text_to_docs(doc)
    try:
        with st.spinner("Indexing document... This may take a while⏳"):
            index = embed_docs(text)
            st.session_state["api_key_configured"] = True
    except OpenAIError as e:
        st.error(e._message)

st.write('To obtain an API Key you must create an OpenAI account at the following link: https://openai.com/api/')
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

def get_text():
    if user_secret:
        st.header("Ask me something about the document:")
        input_text = st.text_area("You:", on_change=clear_submit, key='input_text')
        return input_text
user_input = get_text()

button = st.button("Submit")
if button or st.session_state.get("submit"):
    if not user_input:
        st.error("Please enter a question!")
    else:
        st.session_state["submit"] = True
        sources = search_docs(index, user_input)
        try:
            answer = get_answer(sources, user_input)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(answer["output_text"].split("SOURCES: ")[0])
        except OpenAIError as e:
            st.error(e._message)
        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])-1, -1, -1):
                message(st.session_state["generated"][i], key=str(i))
                message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
