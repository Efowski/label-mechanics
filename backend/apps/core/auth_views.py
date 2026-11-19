from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status


@csrf_protect
def csrf_view(request):
    if request.method != "GET":
        return JsonResponse(
            {"detail": "Method not allowed."},
            status=405,
        )

    get_token(request)
    return JsonResponse({"detail": "CSRF cookie set."})


@require_POST
@csrf_protect
def login_view(request):
    import json

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"detail": "Invalid JSON."},
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"detail": "Expected a JSON object."},
            status=400,
        )

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return JsonResponse(
            {"detail": "Username and password are required."},
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return JsonResponse(
            {"detail": "Invalid credentials."},
            status=400,
        )

    login(request, user)

    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email,
    })


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logged out."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })