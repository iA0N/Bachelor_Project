import base64
import json

import torch
import transformers
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import os

from pymupdf import pymupdf
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import io
import re
from llama_cpp import Llama
import nltk
from torch.backends import mps

from .model_prompts import prompt_bart_large_cnn, prompt_llama_8b
from .models import Document

User = get_user_model()

def get_meta_data(doc_id):
    doc = Document.objects.get(id=doc_id)
    data_url = base64.b64decode(doc.file_data.split(',')[1])
    document = pymupdf.open("pdf", data_url)
    title = document.metadata.get("title")
    author = document.metadata.get("author")
    return len(document), title, author

def store_summary(doc_id, model):
    doc = Document.objects.get(id=doc_id)
    data_url = base64.b64decode(doc.file_data.split(',')[1])
    document = pymupdf.open("pdf", data_url)
    document_text = ""

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        document_text += page.get_text("text")

    summary = ""
    summary_data = []

    match model:
        case 'demo':
            print("Using demo model")
            with open('./example_json.json', 'r') as file:
                summary = json.load(file)[0]["summary"]
            summary_data = summary

        case 'facebook/bart-large-cnn':
            print("Generating summary with facebook/bart-large-cnn")
            summary = prompt_bart_large_cnn(document_text)

        case 'Meta-Llama-3.1-8B-Instruct-Q8_0.gguf':
            print("Generating summary with Meta-Llama-3.1-8B-Instruct-Q8_0")
            summary = prompt_llama_8b(document_text)
            if not summary.endswith(('.', '!', '?')):
                summary += "..."


        case 'llama-bart-combined':
            print("Generating summary with combined pipeline")
            pre_summary = prompt_llama_8b(document_text)
            summary = prompt_bart_large_cnn(pre_summary)

        case _:
            pass

    # nltk.download('punkt') needed only once
    # nltk.download('punkt_tab') needed only once

    if model != "demo":
        summary_sentences = nltk.sent_tokenize(summary)
        summary_data = [{"sentence": item, "candidates": []} for item in summary_sentences]

    if doc != "":
        doc.summary = json.dumps(summary_data)
        doc.save()
