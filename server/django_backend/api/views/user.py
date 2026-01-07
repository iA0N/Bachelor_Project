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

from ..helper import get_meta_data, store_summary, reconstruct_doc
from ..model_prompts import fix, chat_prompt_llama

from ..models import Document, UserAIModel

User = get_user_model()

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_username(request):

    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        return Response(user.username)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_user_documents(request):
    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        docs = Document.objects.filter(user_id=user.id)
        doc_list = []
        for d in docs:
            first_sentence = ""
            if d.summary:
                first_elem = d.summary[0]
                first_sentence = first_elem['sentence']

            doc_list.append({'id': d.id,
                             'file_name': d.file_name,
                             'summary_teaser': first_sentence[:70] + '...',
                             'used_model': d.used_model})
        return Response({'user_docs': doc_list}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
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
                'file_data': reconstruct_doc(doc),
                'summary': "" if doc.summary is None else doc.summary,
                "num_pages": num_pages,
                "title": title,
                "author": author,
                "chat_history": json.loads(doc.chat_history),
                "used_model": doc.used_model
            }
        , status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def delete_user_document(request, doc_id):
    user = User.objects.get(id=request.user.id)
    if request.method == 'DELETE':
        doc = Document.objects.get(id=doc_id, user_id=user.id)

        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)

        doc.delete()
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_csrf_token(request):
    return Response({"csrf_token": csrf.get_token(request)}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_login_status(request):
    return Response({"login_status": request.user.is_authenticated}, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_user_models(request):
    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        user_models = UserAIModel.objects.filter(user=user)
        user_models_list = []
        for model in user_models:
            user_models_list.append(model.filename)

        return Response({"models": user_models_list}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def create_user_model(request):
    if request.method == 'POST':
        user = User.objects.get(id=request.user.id)
        try:
            UserAIModel.objects.get(filename=request.data['filename'], user=user)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        UserAIModel.objects.create(user=user, repo_id=request.data["repo_id"], filename=request.data["filename"])

        user_models = UserAIModel.objects.filter(user=user)
        user_models_list = []
        for model in user_models:
            user_models_list.append(model.filename)

        return Response({"models": user_models_list}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def remove_user_model(request, model):
    user = User.objects.get(id=request.user.id)
    if request.method == 'DELETE':
        UserAIModel.objects.get(filename=model, user=user).delete()
        user_models = UserAIModel.objects.filter(user=user)
        user_models_list = []
        for model in user_models:
            user_models_list.append(model.filename)

        return Response({"models": user_models_list}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
