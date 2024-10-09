from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from controllers.controllers import SearchController
from .enums import SEARCH_MODEL_COMMANDS

@api_view(['POST'])
def register_user(request):
    controller = SearchController.getInstance()
    return controller.invoke_trigger(SEARCH_MODEL_COMMANDS.M_INIT, request)

@api_view(['POST'])
def login_user(request):
    controller = SearchController.getInstance()
    return controller.invoke_trigger(SEARCH_MODEL_COMMANDS.M_LOGIN, request)
