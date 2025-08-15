from django.contrib import admin
from .models import Article
from .models import UserDetails

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'source', 'published_date', 'language', 'author')
	search_fields = ('title', 'content', 'category', 'tags', 'source', 'author')
admin.site.register(UserDetails)
