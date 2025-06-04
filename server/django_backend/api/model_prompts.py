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

from .models import Document

User = get_user_model()

def fix(match):
    return match.group(1) + match.group(2)

def prompt_llama_8b(document_text):
    llm = Llama(
        model_path=f"{os.getcwd()}/api/llms/Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
        n_ctx=4096
    )

    source = document_text[:2000].strip()
    prompt = f'Summarize this text: "{source}"'

    response = llm.create_chat_completion(
        max_tokens=400,
        messages=[
            {
                "role": "system",
                "content": "Your are a simple text summarization system. "
                           "Do not engage with the user in a conversation and just do the summarization task."
                           ". Do not do anything else. Do not mention or include any parts of the prompt in your answer."
                           "Do not cite any pages or persons and just give information about the text itself."
                           "End your output as soon as you finished summarizing and do not say anything else."
                           "Do not tell me you are ready for the next text or say anything else after finishing the summary."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["choices"][0]["message"]["content"].strip()

def prompt_bart_large_cnn(document_text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    document_text = document_text.replace("\n", " ")
    document_text = re.sub(r'\s+', ' ', document_text).strip()
    document_text = re.sub(r'[^a-zA-Z0-9\s.,:?!]+', '', document_text)[:3000]
    summary = summarizer(document_text, max_length=1200, min_length=100, do_sample=False)[0]['summary_text']
    return summary

def chat_prompt_llama_8b(document_obj, prompt, ):
    # https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

    llm = Llama(
        model_path=f"{os.getcwd()}/api/llms/Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
        n_ctx=7000
    )

    data_url = base64.b64decode(document_obj.file_data.split(',')[1])
    document = pymupdf.open("pdf", data_url)
    document_text = ""

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        document_text += page.get_text("text")

    document_text = document_text.replace("\n", " ")
    document_text = re.sub(r'\s+', ' ', document_text).strip()
    document_text = re.sub(r'[^a-zA-Z0-9\s.,:?!]+', '', document_text)[:3000]

    system_prompt = f'Your are a chat bot to answer questions about a document the user uploaded. This is the document the user uploaded: "{document_text}"'
    messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

    response = llm.create_chat_completion(
        max_tokens=800,
        messages=messages
    )

    return response["choices"][0]["message"]["content"].strip()
