from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from .enums import SEARCH_MODEL_COMMANDS
from .serializers import UserSerializer, LoginSerializer

class SearchController:
    _instance = None

    def __init__(self):
        pass

    @staticmethod
    def getInstance():
        if SearchController._instance is None:
            SearchController._instance = SearchController()
        return SearchController._instance

    def invoke_trigger(self, command, request):
        if command == SEARCH_MODEL_COMMANDS.M_INIT:
            return self.register_user(request)
        elif command == SEARCH_MODEL_COMMANDS.M_LOGIN:
            return self.login_user(request)
        else:
            return Response({"error": "Invalid command"}, status=status.HTTP_400_BAD_REQUEST)

    def register_user(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def login_user(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
