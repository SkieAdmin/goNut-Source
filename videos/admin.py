from django.contrib import admin
from .models import Category, Tag, Video, VideoLike, VideoView, Comment, Playlist, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'video_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'uploader', 'views', 'likes', 'quality', 'is_active', 'is_featured', 'created_at']
    list_filter = ['category', 'quality', 'is_active', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['views', 'likes', 'dislikes', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail', 'preview_gif')
        }),
        ('Video Details', {
            'fields': ('duration', 'quality')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Statistics', {
            'fields': ('views', 'likes', 'dislikes'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('uploader', 'is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'content_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'user__username', 'video__title']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['videos']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'video__title']


@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = ['video', 'ip_address', 'user', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['video__title', 'ip_address']


@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'is_like', 'created_at']
    list_filter = ['is_like', 'created_at']
