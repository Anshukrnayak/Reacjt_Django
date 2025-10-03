# urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterAPiView, LoginAPIView, LogoutAPIView, LogoutAllView

urlpatterns = [
    path('api/register/', RegisterAPiView.as_view(), name='register'),
    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('api/logout/', LogoutAPIView.as_view(), name='logout'),
    path('api/logout-all/', LogoutAllView.as_view(), name='logout_all'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

