from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, UserDetails
from .serializers import ArticleSerializer, UserDetailsSerializer

class ArticleListAPIView(generics.ListAPIView):
	serializer_class = ArticleSerializer

	def get_queryset(self):
		queryset = Article.objects.all().order_by('-published_date')
		search = self.request.query_params.get('search', None)
		if search:
			from django.db.models import Q
			queryset = queryset.filter(
				Q(title__icontains=search) |
				Q(content__icontains=search) |
				Q(tags__icontains=search)
			)
		return queryset

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
            img_url = None
            if details.profile_img:
                request_scheme = request.scheme
                request_host = request.get_host()
                img_url = f"{request_scheme}://{request_host}{details.profile_img.url}" if details.profile_img.url else None
            data['profile_img'] = img_url
            return Response(data, status=status.HTTP_200_OK)
        except (User.DoesNotExist, UserDetails.DoesNotExist):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


# Dedicated view for editing profile
from rest_framework.permissions import IsAuthenticated
class EditProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, username):
        # Only allow user to edit their own profile
        if not request.user.is_authenticated or request.user.username != username:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(username=username)
            details = UserDetails.objects.get(user=user)
            data = request.data
            new_username = data.get('username', user.username)
            language = data.get('language', details.language)
            country = data.get('country', details.country)
            categories = data.get('categories', details.categories)
            # Update username if changed and not taken
            if new_username != user.username:
                if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                user.username = new_username
                user.save()
            details.language = language
            details.country = country
            details.categories = categories
            details.save()
            updated = UserDetailsSerializer(details).data
            updated['username'] = user.username
            img_url = None
            if details.profile_img:
                request_scheme = request.scheme
                request_host = request.get_host()
                img_url = f"{request_scheme}://{request_host}{details.profile_img.url}" if details.profile_img.url else None
            updated['profile_img'] = img_url
            return Response(updated, status=status.HTTP_200_OK)
        except (User.DoesNotExist, UserDetails.DoesNotExist):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
