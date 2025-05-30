import base64
import json

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

from .helper import get_meta_data, store_summary
from .model_prompts import fix, chat_prompt_llama_8b

print(torch.backends.mps.is_available())

from .models import Document

User = get_user_model()

@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_username(request):

    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        return Response(user.username)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def get_highlighted_pdf(request):

    if request.method == 'POST':
        doc = Document.objects.get(id=request.data["doc_id"], user_id=request.user.id)
        pdf_data = doc.file_data
        data_url = base64.b64decode(pdf_data.split(',')[1])
        document = pymupdf.open("pdf", data_url)
        search_string = request.data["search_term"]
        search_string = re.sub(r'(\w+)-\n(\w+)', fix, search_string)

        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text_instances = page.search_for(search_string)

            for inst in text_instances:
                page.add_highlight_annot(inst)

        # highlighted_pdf_path = os.path.join('api/pdf', 'highlighted_' + os.path.basename("api/pdf/out.pdf"))
        # print(str(highlighted_pdf_path))
        # document.save(highlighted_pdf_path)
        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        returned_data_url = f"data:application/pdf;base64,{base64_pdf}"
        return JsonResponse({'data_url': returned_data_url}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def store_and_summarize_document(request):
    if request.method == 'POST':
        print("Storing document")
        #request_data = json.loads(json.dumps(request.data))
        #request_data = JSONParser().parse(request.data)
        file_name = request.data["file_name"]
        file_data = request.data["file_data"]

        doc = Document.objects.create(
            user=request.user,
            file_name=file_name,
            file_data=file_data,
            chat_history=json.dumps([])
        )

        store_summary(doc.id, request.data["model"])
        return Response({"id": doc.id}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def get_user_documents(request):

    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        docs = Document.objects.filter(user_id=user.id)
        doc_list = []
        for d in docs:
            first_sentence = ""
            if d.summary:
                first_elem = json.loads(d.summary)[0]
                first_sentence = first_elem['sentence']

            doc_list.append({'id': d.id,
                             'file_name': d.file_name,
                             'summary_teaser': first_sentence[:60] + '...'})
        return Response({'user_docs': doc_list}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def get_user_document(request, doc_id):
    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        doc = Document.objects.get(id=doc_id, user_id=user.id)

        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)

        num_pages, title, author = get_meta_data(doc.id)

        return Response(
            {
                'id': doc.id,
                'file_name': doc.file_name,
                'file_data': doc.file_data,
                'summary': "" if doc.summary is None else json.loads(doc.summary),
                "num_pages": num_pages,
                "title": title,
                "author": author,
                "chat_history": json.loads(doc.chat_history)
            }
        , status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
def delete_user_document(request, doc_id):
    user = User.objects.get(id=request.user.id)
    if request.method == 'DELETE':
        doc = Document.objects.get(id=doc_id, user_id=user.id)

        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)

        doc.delete()
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def send_chat(request):
    if request.method == 'POST':
        doc_id = request.data["doc_id"]
        doc = Document.objects.get(id=doc_id, user_id=request.user.id)
        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)


        chat_msg = request.data["chat_msg"]
        answer = chat_prompt_llama_8b(doc, chat_msg)

        chat_history_json = json.loads(doc.chat_history)
        chat_history_json.append({"role": "user", "content": chat_msg})
        chat_history_json.append({"role": "system", "content": answer})
        doc.chat_history = json.dumps(chat_history_json)
        doc.save()

        return Response({"chat_history": chat_history_json}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)