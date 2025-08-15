from django.db import models
from django.contrib.auth.models import User

class UserDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='details')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, blank=True)
    categories = models.JSONField(default=list, blank=True)
    profile_img = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} details"


class Article(models.Model):
	title = models.CharField(max_length=255)
	image_url = models.URLField(blank=True, null=True)
	content = models.TextField()
	category = models.CharField(max_length=100)
	tags = models.CharField(max_length=255, blank=True, null=True)
	source = models.CharField(max_length=255)
	published_date = models.DateTimeField()
	language = models.CharField(max_length=50)
	author = models.CharField(max_length=255, blank=True, null=True)

	def __str__(self):
		return self.title
