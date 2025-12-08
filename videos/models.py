from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('videos:category', kwargs={'slug': self.slug})

    def video_count(self):
        return self.videos.filter(is_active=True).count()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Video(models.Model):
    QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('4k', '4K Ultra HD'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)

    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/')
    preview_gif = models.FileField(upload_to='previews/', blank=True, null=True)

    duration = models.PositiveIntegerField(default=0, help_text='Duration in seconds')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='720p')

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    tags = models.ManyToManyField(Tag, blank=True, related_name='videos')
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_videos')

    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f"{base_slug}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('videos:watch', kwargs={'slug': self.slug})

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def duration_formatted(self):
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def like_percentage(self):
        total = self.likes + self.dislikes
        if total == 0:
            return 0
        return int((self.likes / total) * 100)


class VideoLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_likes')
    is_like = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video']


class VideoView(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_views')
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']


class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.video.title[:30]}"


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    videos = models.ManyToManyField(Video, blank=True, related_name='playlists')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.user.username}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video']
        ordering = ['-created_at']


# ============ API VIDEO INTERACTIONS ============
# These models track user interactions with external API videos (Eporner, etc.)

class APIVideoView(models.Model):
    """Track view history for API videos"""
    SOURCE_CHOICES = [
        ('eporner', 'Eporner'),
        ('redtube', 'RedTube'),
        ('hentai', 'Hentai'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_video_views')
    video_id = models.CharField(max_length=100)  # External API video ID
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='eporner')
    title = models.CharField(max_length=500, blank=True)  # Cache title for history display
    thumbnail = models.URLField(max_length=500, blank=True)  # Cache thumbnail URL
    duration = models.CharField(max_length=20, blank=True)  # Cache duration
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} watched {self.title[:30]}"


class APIVideoLike(models.Model):
    """Track likes/dislikes for API videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_video_likes')
    video_id = models.CharField(max_length=100)
    source = models.CharField(max_length=20, default='eporner')
    is_like = models.BooleanField(default=True)  # True=like, False=dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video_id', 'source']

    def __str__(self):
        action = 'liked' if self.is_like else 'disliked'
        return f"{self.user.username} {action} {self.video_id}"


class APIVideoFavorite(models.Model):
    """Track favorites for API videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_video_favorites')
    video_id = models.CharField(max_length=100)
    source = models.CharField(max_length=20, default='eporner')
    title = models.CharField(max_length=500, blank=True)  # Cache for display
    thumbnail = models.URLField(max_length=500, blank=True)
    duration = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video_id', 'source']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.title[:30]}"


class APIVideoComment(models.Model):
    """Comments on API videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_video_comments')
    video_id = models.CharField(max_length=100)
    source = models.CharField(max_length=20, default='eporner')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} commented on {self.video_id}"


# ============ MAL-STYLE VIDEO LIST ============
# Track videos in user's list with status and score (like MyAnimeList)

class VideoList(models.Model):
    """MAL-style video list - track videos with status and score"""
    STATUS_CHOICES = [
        ('watching', 'Currently Watching'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
        ('plan_to_watch', 'Plan to Watch'),
    ]

    SOURCE_CHOICES = [
        ('eporner', 'Eporner'),
        ('redtube', 'RedTube'),
        ('hentai', 'Hentai'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_list')
    video_id = models.CharField(max_length=100)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='eporner')

    # Video info cache
    title = models.CharField(max_length=500)
    thumbnail = models.URLField(max_length=500, blank=True)
    duration = models.CharField(max_length=20, blank=True)

    # MAL-style fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan_to_watch')
    score = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-10 rating
    times_watched = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'video_id', 'source']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s list: {self.title[:30]} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-set completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def get_user_stats(cls, user):
        """Get MAL-style statistics for a user"""
        from django.db.models import Avg, Count, Sum

        entries = cls.objects.filter(user=user)
        stats = {
            'total': entries.count(),
            'watching': entries.filter(status='watching').count(),
            'completed': entries.filter(status='completed').count(),
            'on_hold': entries.filter(status='on_hold').count(),
            'dropped': entries.filter(status='dropped').count(),
            'plan_to_watch': entries.filter(status='plan_to_watch').count(),
            'mean_score': entries.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg'] or 0,
            'total_times_watched': entries.aggregate(total=Sum('times_watched'))['total'] or 0,
            'scored_count': entries.filter(score__isnull=False).count(),
        }
        return stats
