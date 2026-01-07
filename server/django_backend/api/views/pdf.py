import base64
import json
import string

import fitz
import icecream
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
from django.middleware import csrf

from ..helper import get_meta_data, store_summary, replace_ligatures, reconstruct_doc
from ..model_prompts import fix, chat_prompt_llama

from ..models import Document

User = get_user_model()

import base64
import json
import string

import fitz
import icecream
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
from django.middleware import csrf

from ..helper import get_meta_data, store_summary, replace_ligatures, reconstruct_doc
from ..model_prompts import fix, chat_prompt_llama

from ..models import Document

User = get_user_model()

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_highlighted_pdf(request):

    if request.method == 'POST':
        doc = Document.objects.get(id=request.data["doc_id"], user_id=request.user.id)
        data_url = doc.file_data
        document = pymupdf.open("pdf", data_url)
        search_string = request.data["search_term"]
        search_string = re.sub(r'(\w+)-\n(\w+)', fix, search_string)
        search_string = replace_ligatures(search_string)
        search_string = search_string.rstrip(string.punctuation)

        full_text = ""
        page_num_start = -1
        word_positions = []

        for page_num in range(len(document)):
            page = document.load_page(page_num)
            words = page.get_text("words")

            # Sort words in proper reading order
            words.sort(key=lambda w: (w[5], w[6], w[7]))

            for w in words:
                x0, y0, x1, y1, word = w[:5]
                norm_word = replace_ligatures(word)

                # Handle spacing between words
                if full_text:
                    full_text += " "

                start_idx = len(full_text)
                full_text += norm_word
                end_idx = len(full_text)

                word_positions.append({
                    "page": page_num,
                    "rect": fitz.Rect(x0, y0, x1, y1),
                    "start": start_idx,
                    "end": end_idx
                })

        # Search in full normalized string
        match_start = full_text.find(search_string)
        if match_start == -1:
            raise Exception("Search string not found.")

        match_end = match_start + len(search_string)

        # Find all words that fall within the match range
        for word_info in word_positions:
            if word_info["end"] <= match_start:
                continue
            if word_info["start"] >= match_end:
                break
            page = document[word_info["page"]]
            page.add_highlight_annot(word_info["rect"])
            if page_num_start == -1:
                page_num_start = page.number

        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        returned_data_url = f"data:application/pdf;base64,{base64_pdf}"
        return JsonResponse({'data_url': returned_data_url, 'page_num_start': page_num_start + 1}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def store_and_summarize_document(request):
    if request.method == 'POST':
        file_name = request.data["file_name"]
        file_data = request.data["file_data"]

        data = file_data.split(',')
        content_type = data[0]
        document_data = data[1]
        data_url = base64.b64decode(document_data)

        doc = Document.objects.create(
            user=request.user,
            file_name=file_name,
            file_data=data_url,
            content_type=content_type,
            chat_history=json.dumps([])
        )

        store_summary(doc.id, request.data["model"], request.user)
        reconstruct_doc(doc)
        return Response({"id": doc.id}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
