from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, UserDetails
from .serializers import ArticleSerializer, UserDetailsSerializer

class ArticleListAPIView(generics.ListAPIView):
	serializer_class = ArticleSerializer
	filter_backends = [SearchFilter]
	search_fields = ['title', 'content', 'tags']

	def get_queryset(self):
		return Article.objects.all().order_by('-published_date')

class ArticleDetailAPIView(generics.RetrieveAPIView):
	queryset = Article.objects.all()
	serializer_class = ArticleSerializer


# Login API
class LoginAPIView(APIView):
	def post(self, request):
		username = request.data.get('username')
		password = request.data.get('password')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			dj_login(request, user)
			return Response({'user': {'username': user.username}}, status=status.HTTP_200_OK)
		return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# Signup API
class SignupAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        email = request.data.get('email', '')
        country = request.data.get('country', '')
        language = request.data.get('language', '')
        categories = request.data.get('categories', [])
        profile_img = request.FILES.get('profile_img')

        # Fix: parse categories if sent as JSON string
        import json
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except Exception:
                categories = []

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        details = UserDetails.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            country=country,
            language=language,
            categories=categories if isinstance(categories, list) else [],
            profile_img=profile_img
        )
        # Fix: return absolute image URL for frontend
        img_url = None
        if details.profile_img:
            request_scheme = request.scheme
            request_host = request.get_host()
            img_url = f"{request_scheme}://{request_host}{details.profile_img.url}" if details.profile_img.url else None
        return Response({
            'user': {
                'username': user.username,
                'first_name': details.first_name,
                'last_name': details.last_name,
                'email': details.email,
                'country': details.country,
                'language': details.language,
                'categories': details.categories,
                'profile_img': img_url
            }
        }, status=status.HTTP_201_CREATED)

class ProfileAPIView(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            details = UserDetails.objects.get(user=user)
            data = UserDetailsSerializer(details).data
            data['username'] = user.username
            # Fix: return absolute image URL for frontend
            img_url = None
            if details.profile_img:
                request_scheme = request.scheme
                request_host = request.get_host()
                img_url = f"{request_scheme}://{request_host}{details.profile_img.url}" if details.profile_img.url else None
            data['profile_img'] = img_url
            return Response(data, status=status.HTTP_200_OK)
        except (User.DoesNotExist, UserDetails.DoesNotExist):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
