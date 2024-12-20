from django.contrib import admin
from .models import User, Rating

admin.site.register(User)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'rated_user', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('rater__email', 'rated_user__email', 'review')
    date_hierarchy = 'created_at'