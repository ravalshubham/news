from django.urls import path
from .views import ArticleListAPIView, ArticleDetailAPIView, LoginAPIView, SignupAPIView
from .views import ProfileAPIView, EditProfileAPIView

urlpatterns = [
    path('articles/', ArticleListAPIView.as_view(), name='article-list'),
    path('articles/<int:pk>/', ArticleDetailAPIView.as_view(), name='article-detail'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('profile/<str:username>/', ProfileAPIView.as_view(), name='profile'),
    path('profile/<str:username>/edit/', EditProfileAPIView.as_view(), name='profile-edit'),
]
