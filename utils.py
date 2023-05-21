from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain import OpenAI, Cohere
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS, VectorStore
import docx2txt
from typing import List, Dict, Any
import re
import numpy as np
from io import StringIO
from io import BytesIO
import streamlit as st
from prompts import STUFF_PROMPT
from pypdf import PdfReader
from openai.error import AuthenticationError

@st.experimental_memo()
def parse_docx(file: BytesIO) -> str:
    text = docx2txt.process(file)
    # Remove multiple newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text


@st.experimental_memo()
def parse_pdf(file: BytesIO) -> List[str]:
    pdf = PdfReader(file)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        # Merge hyphenated words
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        # Fix newlines in the middle of sentences
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        # Remove multiple newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)

        output.append(text)

    return output


@st.experimental_memo()
def parse_txt(file: BytesIO) -> str:
    text = file.read().decode("utf-8")
    # Remove multiple newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text

@st.experimental_memo()
def parse_csv(uploaded_file):
    # To read file as bytes:
    #bytes_data = uploaded_file.getvalue()
    #st.write(bytes_data)

    # To convert to a string based IO:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    #st.write(stringio)

    # To read file as string:
    string_data = stringio.read()
    #st.write(string_data)

    # Can be used wherever a "file-like" object is accepted:
    # dataframe = pd.read_csv(uploaded_file)
    return string_data

@st.experimental_memo()
def parse_any(uploaded_file):
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    string_data = stringio.read()
    return string_data


@st.cache(allow_output_mutation=True)
def text_to_docs(text: str) -> List[Document]:
    """Converts a string or list of strings to a list of Documents
    with metadata."""
    if isinstance(text, str):
        # Take a single string as one page
        text = [text]
    page_docs = [Document(page_content=page) for page in text]

    # Add page numbers as metadata
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    # Split pages into chunks
    doc_chunks = []

    for doc in page_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            max_chunks=None,
        )
        chunks = text_splitter.split(doc)
        doc_chunks.extend(chunks)

    return doc_chunks


@st.experimental_memo()
def embed_text(text: str, model: Any) -> List[List[float]]:
    """Embeds a string or list of strings using the specified model."""
    if isinstance(text, str):
        # Take a single string as one page
        text = [text]
    embeddings = model.embed_documents(text)
    return embeddings


def wrap_text_in_html(text: str) -> str:
    """Wrap text in HTML <pre> tag for rendering as monospace."""
    return f"<pre>{text}</pre>"


def main():
    st.title("Language Chain Demo")
    st.markdown(STUFF_PROMPT)

    file = st.file_uploader("Upload a file", type=["txt", "pdf", "docx", "csv"])

    if file is not None:
        if file.type == "application/pdf":
            texts = parse_pdf(file)
        elif file.type == "text/plain":
            texts = [parse_txt(file)]
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            texts = [parse_docx(file)]
        elif file.type == "text/csv":
            texts = [parse_csv(file)]
        else:
            texts = [parse_any(file)]

        docs = text_to_docs(texts)
        st.markdown(f"**Uploaded Text:**\n\n{wrap_text_in_html(docs[0].content)}")

        # Initialize the embedding model
        embedding_model = OpenAIEmbeddings(openai_api_key="your-openai-api-key")

        # Embed the documents
        embeddings = embed_text(docs, embedding_model)

        # Perform downstream tasks using the embeddings
        # ...
        # ...


if __name__ == "__main__":
    main()
