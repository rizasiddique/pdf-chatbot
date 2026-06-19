from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from groq import Groq
import chromadb
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://merry-moxie-a00593.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChromaDB setup
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="pdf_chat"
)

# Groq setup
import os

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")

)

@app.get("/")
def home():
    return {"message": "PDF Chatbot Running"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    pdf_data = await file.read()

    reader = PdfReader(io.BytesIO(pdf_data))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text

    chunks = text.split("\n\n")

    try:
        collection.delete(
            ids=collection.get()["ids"]
        )
    except:
        pass

    ids = [str(i) for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        ids=ids
    )

    return {
        "message": "PDF uploaded and stored successfully"
    }

@app.post("/ask")
async def ask_question(data: dict):

    question = data["question"]

    results = collection.query(
        query_texts=[question],
        n_results=1
    )

    context = results["documents"][0][0]

    prompt = f"""
Answer ONLY using the context below.

Context:
{context}

Question:
{question}
"""

    response = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile"
    )

    return {
        "answer":
        response.choices[0].message.content
    }