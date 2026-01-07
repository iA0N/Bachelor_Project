import base64
import json
from django.contrib.auth import get_user_model
from pymupdf import pymupdf
import nltk

from .model_prompts import prompt_bart_large_cnn, prompt_llama_model
from .models import Document, UserAIModel

User = get_user_model()
TESTING = True

LIGATURES = {
        '\uFB00': 'ff',
        '\uFB01': 'fi',
        '\uFB02': 'fl',
        '\uFB03': 'ffi',
        '\uFB04': 'ffl',
        '\uFB05': 'ft',
        '\uFB06': 'st'
    }

QUOTES = {
    '\u2019': "'",  # right single quote
    '\u2018': "'",  # left single quote
    '\u02BC': "'",  # modifier letter apostrophe
    '\u2032': "'",  # prime
    '`': "'",  # backtick
    '’': "'",  # literal right single quote

    '\u201C': "'",  # left double quote
    '\u201D': "'",  # right double quote
    '\u201E': "'",  # low double quote
    '\u2033': "'",  # double prime
    '“': "'",  # literal
    '”': "'",  # literal
    '„': "'",  # literal
    '″': "'",  # literal
}

def get_meta_data(doc_id):
    doc = Document.objects.get(id=doc_id)
    # data_url = base64.b64decode(doc.file_data.split(',')[1])
    document = pymupdf.open("pdf", doc.file_data)
    title = document.metadata.get("title")
    author = document.metadata.get("author")
    return len(document), title, author

def store_summary(doc_id, model, user):
    doc = Document.objects.get(id=doc_id)
    # data_url = base64.b64decode(doc.file_data.split(',')[1])
    document = pymupdf.open("pdf", doc.file_data)
    document_text = ""

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        document_text += page.get_text("text")

    for lig, repl in LIGATURES.items():
        document_text = document_text.replace(lig, repl)

    summary = ""
    summary_data = []

    if not TESTING:
        # For demo purposes, just a json file gets read in which represents the
        # model response normally obtained from the model itself.

        with open('./example.json', 'r') as file:
            summary = json.load(file)[0]["summary"]
        summary_data = summary

    else:
        # For testing purposes also custom models can be used to generate summaries, but they will not
        # provide the additional information of source origins.
        # Currently the chosen 'chat model' will be reused as a summarization model.

        try:
            user_model = UserAIModel.objects.get(filename=model, user=user)
            summary = prompt_llama_model(document_text, user_model.repo_id, user_model.filename)
        except:
            summary = "Error during summary generation, are you sure the provided repo_id and filename is correct?"


    # nltk.download('punkt') needed only once
    # nltk.download('punkt_tab') needed only once

    if TESTING:
        # To store the response (the summary) in the correct format, even though the candidates will be empty.
        summary_sentences = nltk.sent_tokenize(summary)
        summary_data = [{"sentence": item, "candidates": []} for item in summary_sentences]

    if doc != "":
        doc.summary = json.loads(json.dumps(summary_data))
        doc.used_model = model
        doc.save()

def replace_ligatures(text):
    for ligature, replacement in LIGATURES.items():
        text = text.replace(ligature, replacement)

    for orig, std in QUOTES.items():
        text = text.replace(orig, std)

    return text

def reconstruct_doc(doc):
    document_data = doc.file_data
    content_type = doc.content_type
    reconstructed_base64 = content_type + "," + base64.b64encode(document_data).decode('utf-8')
    return reconstructed_base64