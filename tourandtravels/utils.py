from rest_framework.views import exception_handler
from rest_framework.pagination import PageNumberPagination
import traceback
import sys


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 500


def custom_exception_handler(exc, context):
    print("====== DRF EXCEPTION ======", file=sys.stderr)
    traceback.print_exc()
    print("===========================", file=sys.stderr)
    return exception_handler(exc, context)
