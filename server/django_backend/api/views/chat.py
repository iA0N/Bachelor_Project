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

from ..helper import get_meta_data, store_summary, replace_ligatures
from ..model_prompts import fix, chat_prompt_llama

from ..models import Document, UserAIModel

User = get_user_model()

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def send_chat(request):
    if request.method == 'POST':
        doc_id = request.data["doc_id"]
        doc = Document.objects.get(id=doc_id, user_id=request.user.id)
        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            chat_msg = request.data["chat_msg"]
            model = UserAIModel.objects.get(filename=doc.used_model, user=request.user)
            answer = chat_prompt_llama(doc, chat_msg, model.repo_id, model.filename)
        except:
            answer = "An error occurred during answer generation."

        chat_history_json = json.loads(doc.chat_history)
        chat_history_json.append({"role": "user", "content": chat_msg})
        chat_history_json.append({"role": "system", "content": answer})
        doc.chat_history = json.dumps(chat_history_json)
        doc.save()

        return Response({"chat_history": chat_history_json}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)