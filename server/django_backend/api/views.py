import base64

from django.http import HttpResponse, JsonResponse
import os
from pymupdf import pymupdf
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.decorators import api_view
import io


@api_view(['POST'])
def highlight_pdf(request):
    try:
        if request.method == 'POST':
            request_data = JSONParser().parse(request)
            pdf_data = request_data["pdf_data"]
            data_url = base64.b64decode(pdf_data.split(',')[1])
            document = pymupdf.open("pdf", data_url)
            # document = pymupdf.open("api/pdf/Generative AI Models Opportunities and risks for industry.pdf")

            search_string = "Lorem ipsum dolor sit amet"

            # Or array

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

    except Exception as e:
        print(e)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
