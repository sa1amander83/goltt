from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts import views

app_name = "accounts"


urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("signout/", views.signout, name="signout"),
    path('auth/',include('djoser.urls')),
    path("token/", TokenObtainPairView.as_view(),name='token_obtain_view'),
        path("token/refresh/", TokenRefreshView.as_view(),name='token_refresh_view')


]   
