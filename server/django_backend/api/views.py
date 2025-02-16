import base64
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import os

from nltk import sent_tokenize
from pymupdf import pymupdf
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from transformers import pipeline
import io
import re
from llama_cpp import Llama
import nltk

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


def summarize(doc_id, model):
    doc = Document.objects.get(id=doc_id)
    data_url = base64.b64decode(doc.file_data.split(',')[1])
    document = pymupdf.open("pdf", data_url)
    document_text = ""

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        document_text += page.get_text("text")

    summary = ""

    match model:
        case 'facebook/bart-large-cnn':
            print("Generating summary with facebook/bart-large-cnn")
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device="cpu")
            document_text = document_text.replace("\n", " ")
            document_text = re.sub(r'\s+', ' ', document_text).strip()
            document_text = re.sub(r'[^a-zA-Z0-9\s.,:?!]+', '', document_text)[:3000]
            summary = summarizer(document_text, max_length=1200, min_length=100, do_sample=False)[0]['summary_text']

        case 'Meta-Llama-3.1-8B-Instruct-Q8_0.gguf':
            print("Generating summary with Meta-Llama-3.1-8B-Instruct-Q8_0")
            llm = Llama(
                model_path="/home/ia0n/bakk/Bachelor_Project/server/django_backend/api/llms/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf",
                n_ctx=4096,
                #n_threads=14,
            )

            source = document_text[:2000]
            print(source)
            summary = llm(f'I want you to summarize a text that i will give you. Do not do anything else. Do not mention or include any parts of the prompt in your answer. Do not cite any pages or persons and just give information about the text itself. End your output as soon as you finished summarizing and do not say anything else. Do not tell me you are ready for the next text or say anything else after finishing the summary. This is the text to process: "{source}"', max_tokens=200)
            print(summary)
            summary = summary['choices'][0]['text']
            if not summary.endswith(('.', '!', '?')):
                summary += "..."
            if summary[0:3] == ' . ':
                summary = summary[3:]

        case _:
            pass

    nltk.download('punkt')
    nltk.download('punkt_tab')
    summary_sentences = sent_tokenize(summary)

    if doc != "":
        doc.summary = json.dumps(summary_sentences)
        doc.save()

    return summary_sentences


@api_view(['POST'])
def store_and_summarize(request):

    if request.method == 'POST':

        print("Storing document")
        #request_data = json.loads(json.dumps(request.data))
        #request_data = JSONParser().parse(request.data)
        file_name = request.data["file_name"]
        file_data = request.data["file_data"]

        doc = Document.objects.create(
            user=request.user,
            file_name=file_name,
            file_data=file_data
        )

        summary = summarize(doc.id, request.data["model"])
        return Response({"summary": summary}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def get_user_documents(request):

    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        docs = Document.objects.filter(user_id=user.id)
        doc_list = []
        for d in docs:
            doc_list.append({'id': d.id,
                             'file_name': d.file_name,
                             'summary_teaser': "" if d.summary is None else json.loads(d.summary)[0][:30] + '...'})
        return Response({'user_docs': doc_list}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def get_user_document(request, doc_id):

    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        doc = Document.objects.get(id=doc_id, user_id=user.id)
        return Response(
            {
                'id': doc.id,
                'file_name': doc.file_name,
                'file_data': doc.file_data,
                'summary': "" if doc.summary is None else json.loads(doc.summary)
            }
        , status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def fix(match):
    return match.group(1) + match.group(2)