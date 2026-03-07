from rest_framework.views import exception_handler
import traceback
import sys

def custom_exception_handler(exc, context):
    print("====== DRF EXCEPTION ======", file=sys.stderr)
    traceback.print_exc()
    print("===========================", file=sys.stderr)
    return exception_handler(exc, context)
