from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Dokploy / Docker health check endpoint."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "connected"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=503)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('', include('farm.urls')),
]
