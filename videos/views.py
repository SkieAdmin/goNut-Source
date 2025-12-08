from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.db.models import Q, F
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import json
from .models import (
    Video, Category, Tag, Comment, VideoLike, Favorite, VideoView,
    APIVideoView, APIVideoLike, APIVideoFavorite, APIVideoComment, VideoList
)
from .services import EpornerAPI, HanimeAPI, RedTubeAPI, PornstarService, parse_duration, get_embed_url, get_quality_label


def get_user_gay_param(request):
    """Get the user's content preference for Eporner API gay parameter"""
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        return request.user.profile.get_api_gay_param()
    return 0  # Default to straight content


def home_view(request):
    """Homepage with mixed API videos from Eporner and RedTube"""
    import random
    from urllib.parse import urlencode

    # Get user's content preference
    gay_param = get_user_gay_param(request)

    # Get videos from Eporner (filtered by user preference)
    eporner_trending = EpornerAPI.get_trending(per_page=8, gay=gay_param)
    eporner_latest = EpornerAPI.get_latest(per_page=8, gay=gay_param)
    eporner_top = EpornerAPI.get_top_rated(per_page=8, gay=gay_param)

    # Get videos from RedTube
    redtube_trending = RedTubeAPI.get_trending(page=1)
    redtube_latest = RedTubeAPI.get_latest(page=1)

    # Process Eporner videos - add source tag and watch URL
    def process_eporner(videos):
        processed = []
        for v in videos:
            v['source'] = 'eporner'
            v['watch_url'] = f"/watch/{v.get('id')}/"
            processed.append(v)
        return processed

    # Process RedTube videos - normalize format and add watch URL with fallback params
    def process_redtube(videos):
        processed = []
        for v in videos:
            # Build URL with fallback query params
            params = urlencode({
                'title': v.get('title', ''),
                'thumb': v.get('thumb', ''),
                'duration': v.get('duration', ''),
                'views': v.get('views', 0),
                'rating': v.get('rating', 0),
            })
            processed.append({
                'id': v.get('id'),
                'title': v.get('title', ''),
                'default_thumb': {'src': v.get('thumb', '')},
                'views': v.get('views', 0),
                'rate': v.get('rating', 0),
                'length_min': v.get('duration', ''),
                'keywords': '',
                'source': 'redtube',
                'watch_url': f"/redtube/watch/{v.get('id')}/?{params}"
            })
        return processed

    # Mix trending videos
    trending_eporner = process_eporner(eporner_trending.get('videos', [])[:6] if eporner_trending else [])
    trending_redtube = process_redtube(redtube_trending.get('videos', [])[:6] if redtube_trending else [])
    mixed_trending = trending_eporner + trending_redtube
    random.shuffle(mixed_trending)

    # Mix newest videos
    newest_eporner = process_eporner(eporner_latest.get('videos', [])[:6] if eporner_latest else [])
    newest_redtube = process_redtube(redtube_latest.get('videos', [])[:6] if redtube_latest else [])
    mixed_newest = newest_eporner + newest_redtube
    random.shuffle(mixed_newest)

    # Featured from top rated (Eporner only as they have better featured content)
    featured_videos = process_eporner(eporner_top.get('videos', [])[:8] if eporner_top else [])

    # Get popular pornstars for the horizontal scroller
    popular_pornstars = PornstarService.get_popular(limit=20)

    context = {
        'trending_videos': mixed_trending[:12],
        'newest_videos': mixed_newest[:12],
        'featured_videos': featured_videos,
        'popular_pornstars': popular_pornstars,
    }
    return render(request, 'videos/home.html', context)


def watch_view(request, video_id):
    """Watch video page using embed"""
    video_data = EpornerAPI.get_video_by_id(video_id)

    if not video_data or 'error' in video_data:
        return render(request, 'videos/error.html', {'message': 'Video not found'})

    # Log view for authenticated users
    if request.user.is_authenticated:
        APIVideoView.objects.create(
            user=request.user,
            video_id=video_id,
            source='eporner',
            title=video_data.get('title', ''),
            thumbnail=video_data.get('default_thumb', {}).get('src', ''),
            duration=video_data.get('length_min', '')
        )

    # Get related videos
    keywords = video_data.get('keywords', '')
    first_keyword = keywords.split(',')[0].strip() if keywords else ''
    related_data = EpornerAPI.search(query=first_keyword, per_page=12) if first_keyword else None

    # Process keywords into a list for the template
    tags_list = [tag.strip() for tag in keywords.split(',') if tag.strip()] if keywords else []

    # Get user interaction data
    user_like = None
    is_favorited = False
    if request.user.is_authenticated:
        like_obj = APIVideoLike.objects.filter(user=request.user, video_id=video_id, source='eporner').first()
        user_like = like_obj.is_like if like_obj else None
        is_favorited = APIVideoFavorite.objects.filter(user=request.user, video_id=video_id, source='eporner').exists()

    # Get comments for this video
    comments = APIVideoComment.objects.filter(video_id=video_id, source='eporner', is_active=True).select_related('user')[:50]

    # Count likes/dislikes from our database
    likes_count = APIVideoLike.objects.filter(video_id=video_id, source='eporner', is_like=True).count()
    dislikes_count = APIVideoLike.objects.filter(video_id=video_id, source='eporner', is_like=False).count()

    context = {
        'video': video_data,
        'embed_url': get_embed_url(video_id),
        'related_videos': related_data.get('videos', [])[:12] if related_data else [],
        'tags_list': tags_list,
        'user_like': user_like,
        'is_favorited': is_favorited,
        'comments': comments,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
    }
    return render(request, 'videos/watch_api.html', context)


def trending_view(request):
    """Trending videos from API"""
    page = int(request.GET.get('page', 1))
    gay_param = get_user_gay_param(request)
    data = EpornerAPI.get_trending(page=page, per_page=24, gay=gay_param)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 24 < total_count,
        'has_prev': page > 1,
        'page_title': 'Trending Now',
        'page_icon': 'bi-fire text-danger',
    }
    return render(request, 'videos/video_list_api.html', context)


def newest_view(request):
    """Newest videos from API"""
    page = int(request.GET.get('page', 1))
    gay_param = get_user_gay_param(request)
    data = EpornerAPI.get_latest(page=page, per_page=24, gay=gay_param)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 24 < total_count,
        'has_prev': page > 1,
        'page_title': 'Newest Videos',
        'page_icon': 'bi-clock text-info',
    }
    return render(request, 'videos/video_list_api.html', context)


def top_rated_view(request):
    """Top rated videos from API"""
    page = int(request.GET.get('page', 1))
    gay_param = get_user_gay_param(request)
    data = EpornerAPI.get_top_rated(page=page, per_page=24, gay=gay_param)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 24 < total_count,
        'has_prev': page > 1,
        'page_title': 'Top Rated',
        'page_icon': 'bi-star text-warning',
    }
    return render(request, 'videos/video_list_api.html', context)


def search_view(request):
    """Search videos from both Eporner and RedTube APIs"""
    import random
    from urllib.parse import urlencode

    query = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    gay_param = get_user_gay_param(request)

    videos = []
    total_count = 0

    if query:
        # Search Eporner API
        eporner_data = EpornerAPI.search(query=query, page=page, per_page=12, gay=gay_param)
        eporner_videos = eporner_data.get('videos', []) if eporner_data else []
        eporner_total = int(eporner_data.get('total_count', 0)) if eporner_data else 0

        # Search RedTube API
        redtube_data = RedTubeAPI.search(query=query, page=page)
        redtube_videos = redtube_data.get('videos', []) if redtube_data else []
        redtube_total = int(redtube_data.get('count', 0)) if redtube_data else 0

        # Process Eporner videos
        for v in eporner_videos:
            v['source'] = 'eporner'
            v['watch_url'] = f"/watch/{v.get('id')}/"
            videos.append(v)

        # Process RedTube videos to match Eporner format
        for v in redtube_videos:
            params = urlencode({
                'title': v.get('title', ''),
                'thumb': v.get('thumb', ''),
                'duration': v.get('duration', ''),
                'views': v.get('views', 0),
                'rating': v.get('rating', 0),
            })
            videos.append({
                'id': v.get('id'),
                'title': v.get('title', ''),
                'default_thumb': {'src': v.get('thumb', '')},
                'views': v.get('views', 0),
                'rate': v.get('rating', 0),
                'length_min': v.get('duration', ''),
                'keywords': '',
                'source': 'redtube',
                'watch_url': f"/redtube/watch/{v.get('id')}/?{params}"
            })

        # Shuffle to mix both sources
        random.shuffle(videos)
        total_count = eporner_total + redtube_total

    context = {
        'videos': videos,
        'query': query,
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 24 < total_count,
        'has_prev': page > 1,
    }
    return render(request, 'videos/search_api.html', context)


def category_list_view(request):
    """List all categories"""
    categories = [
        {'name': 'Amateur', 'slug': 'amateur', 'icon': 'bi-camera-video'},
        {'name': 'Anal', 'slug': 'anal', 'icon': 'bi-circle'},
        {'name': 'Asian', 'slug': 'asian', 'icon': 'bi-globe-asia-australia'},
        {'name': 'Babe', 'slug': 'babe', 'icon': 'bi-star'},
        {'name': 'BBW', 'slug': 'bbw', 'icon': 'bi-heart'},
        {'name': 'Big Tits', 'slug': 'big-tits', 'icon': 'bi-suit-heart'},
        {'name': 'Blonde', 'slug': 'blonde', 'icon': 'bi-brightness-high'},
        {'name': 'Blowjob', 'slug': 'blowjob', 'icon': 'bi-droplet'},
        {'name': 'Brunette', 'slug': 'brunette', 'icon': 'bi-moon'},
        {'name': 'Ebony', 'slug': 'ebony', 'icon': 'bi-gem'},
        {'name': 'Fetish', 'slug': 'fetish', 'icon': 'bi-lock'},
        {'name': 'Hardcore', 'slug': 'hardcore', 'icon': 'bi-fire'},
        {'name': 'Latina', 'slug': 'latina', 'icon': 'bi-sun'},
        {'name': 'Lesbian', 'slug': 'lesbian', 'icon': 'bi-hearts'},
        {'name': 'MILF', 'slug': 'milf', 'icon': 'bi-award'},
        {'name': 'Pornstar', 'slug': 'pornstar', 'icon': 'bi-star-fill'},
        {'name': 'POV', 'slug': 'pov', 'icon': 'bi-eye'},
        {'name': 'Redhead', 'slug': 'redhead', 'icon': 'bi-flower1'},
        {'name': 'Teen (18+)', 'slug': 'teen', 'icon': 'bi-person'},
        {'name': 'Threesome', 'slug': 'threesome', 'icon': 'bi-people'},
    ]
    return render(request, 'videos/categories_api.html', {'categories': categories})


def category_detail_view(request, slug):
    """Videos by category from API"""
    page = int(request.GET.get('page', 1))
    gay_param = get_user_gay_param(request)
    data = EpornerAPI.search(query=slug, page=page, per_page=24, gay=gay_param)

    category_names = {
        'amateur': 'Amateur', 'anal': 'Anal', 'asian': 'Asian', 'babe': 'Babe',
        'bbw': 'BBW', 'big-tits': 'Big Tits', 'blonde': 'Blonde', 'blowjob': 'Blowjob',
        'brunette': 'Brunette', 'ebony': 'Ebony', 'fetish': 'Fetish', 'hardcore': 'Hardcore',
        'latina': 'Latina', 'lesbian': 'Lesbian', 'milf': 'MILF', 'pornstar': 'Pornstar',
        'pov': 'POV', 'redhead': 'Redhead', 'teen': 'Teen (18+)', 'threesome': 'Threesome',
    }

    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 24 < total_count,
        'has_prev': page > 1,
        'category_name': category_names.get(slug, slug.title()),
        'category_slug': slug,
    }
    return render(request, 'videos/category_detail_api.html', context)


# ============ HENTAI SECTION (Hanime.tv API) ============

def hentai_home_view(request):
    """Hentai homepage"""
    trending_data = HanimeAPI.get_trending(page=0)
    latest_data = HanimeAPI.get_latest(page=0)

    context = {
        'trending_videos': trending_data.get('videos', [])[:12] if trending_data else [],
        'newest_videos': latest_data.get('videos', [])[:12] if latest_data else [],
    }
    return render(request, 'videos/hentai/home.html', context)


def hentai_browse_view(request):
    """Browse hentai videos"""
    page = int(request.GET.get('page', 0))
    order = request.GET.get('order', 'created_at_unix')
    data = HanimeAPI.search(page=page, order_by=order)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'total_pages': data.get('pages', 0) if data else 0,
        'has_next': page < (data.get('pages', 0) - 1) if data else False,
        'has_prev': page > 0,
        'page_title': 'Browse Hentai',
        'page_icon': 'bi-collection text-pink',
    }
    return render(request, 'videos/hentai/browse.html', context)


def hentai_trending_view(request):
    """Trending hentai"""
    page = int(request.GET.get('page', 0))
    data = HanimeAPI.get_trending(page=page)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'total_pages': data.get('pages', 0) if data else 0,
        'has_next': page < (data.get('pages', 0) - 1) if data else False,
        'has_prev': page > 0,
        'page_title': 'Trending Hentai',
        'page_icon': 'bi-fire text-danger',
    }
    return render(request, 'videos/hentai/browse.html', context)


def hentai_newest_view(request):
    """Newest hentai releases"""
    page = int(request.GET.get('page', 0))
    data = HanimeAPI.get_latest(page=page)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'total_pages': data.get('pages', 0) if data else 0,
        'has_next': page < (data.get('pages', 0) - 1) if data else False,
        'has_prev': page > 0,
        'page_title': 'New Releases',
        'page_icon': 'bi-clock text-info',
    }
    return render(request, 'videos/hentai/browse.html', context)


def hentai_watch_view(request, slug):
    """Watch hentai video"""
    video_data = HanimeAPI.get_video_by_slug(slug)

    if not video_data:
        return render(request, 'videos/error.html', {'message': 'Video not found'})

    # Get related videos by first tag
    tags = video_data.get('tags', [])
    first_tag = tags[0] if tags else None
    related_data = HanimeAPI.get_by_tag(first_tag) if first_tag else None

    context = {
        'video': video_data,
        'related_videos': related_data.get('videos', [])[:12] if related_data else [],
        'episodes': video_data.get('episodes', []),
    }
    return render(request, 'videos/hentai/watch.html', context)


def hentai_tag_view(request, tag):
    """Hentai videos by tag"""
    page = int(request.GET.get('page', 0))
    data = HanimeAPI.get_by_tag(tag, page=page)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'total_pages': data.get('pages', 0) if data else 0,
        'has_next': page < (data.get('pages', 0) - 1) if data else False,
        'has_prev': page > 0,
        'page_title': tag.replace('-', ' ').title(),
        'tag_slug': tag,
    }
    return render(request, 'videos/hentai/tag.html', context)


def hentai_tags_view(request):
    """List all hentai tags"""
    tags = [
        {'name': tag.replace('-', ' ').title(), 'slug': tag}
        for tag in HanimeAPI.TAGS
    ]
    return render(request, 'videos/hentai/tags.html', {'tags': tags})


def hentai_search_view(request):
    """Search hentai videos"""
    query = request.GET.get('q', '')
    page = int(request.GET.get('page', 0))

    if query:
        data = HanimeAPI.search(query=query, page=page)
        videos = data.get('videos', []) if data else []
        total_count = int(data.get('total_count', 0)) if data else 0
        total_pages = data.get('pages', 0) if data else 0
    else:
        videos = []
        total_count = 0
        total_pages = 0

    context = {
        'videos': videos,
        'query': query,
        'total_count': total_count,
        'current_page': page,
        'total_pages': total_pages,
        'has_next': page < (total_pages - 1),
        'has_prev': page > 0,
    }
    return render(request, 'videos/hentai/search.html', context)


# ============ REDTUBE SECTION ============

def redtube_home_view(request):
    """RedTube homepage"""
    trending_data = RedTubeAPI.get_trending(page=1)
    latest_data = RedTubeAPI.get_latest(page=1)

    context = {
        'trending_videos': trending_data.get('videos', [])[:12] if trending_data else [],
        'newest_videos': latest_data.get('videos', [])[:12] if latest_data else [],
    }
    return render(request, 'videos/redtube/home.html', context)


def redtube_browse_view(request):
    """Browse RedTube videos"""
    page = int(request.GET.get('page', 1))
    ordering = request.GET.get('order', 'newest')
    data = RedTubeAPI.search(page=page, ordering=ordering)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 20 < total_count,
        'has_prev': page > 1,
        'page_title': 'Browse Videos',
        'page_icon': 'bi-collection text-danger',
    }
    return render(request, 'videos/redtube/browse.html', context)


def redtube_watch_view(request, video_id):
    """Watch RedTube video"""
    video_data = RedTubeAPI.get_video_by_id(video_id)

    # Create direct embed URL (this always works if video exists on RedTube)
    embed_url = f"https://embed.redtube.com/?id={video_id}"

    # If API failed to get video details, create fallback data from query params
    if not video_data:
        # Try to get info from query parameters (passed from video cards)
        video_data = {
            'id': video_id,
            'title': request.GET.get('title', f'RedTube Video {video_id}'),
            'thumb': request.GET.get('thumb', ''),
            'duration': request.GET.get('duration', ''),
            'views': request.GET.get('views', '0'),
            'rating': request.GET.get('rating', '0'),
            'url': f'https://www.redtube.com/{video_id}',
        }

    # Get related videos
    related_data = RedTubeAPI.get_latest(page=1)

    context = {
        'video': video_data,
        'embed_url': embed_url,
        'related_videos': related_data.get('videos', [])[:12] if related_data else [],
    }
    return render(request, 'videos/redtube/watch.html', context)


def redtube_search_view(request):
    """Search RedTube videos"""
    query = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))

    if query:
        data = RedTubeAPI.search(query=query, page=page)
        videos = data.get('videos', []) if data else []
        total_count = int(data.get('total_count', 0)) if data else 0
    else:
        videos = []
        total_count = 0

    context = {
        'videos': videos,
        'query': query,
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 20 < total_count,
        'has_prev': page > 1,
    }
    return render(request, 'videos/redtube/search.html', context)


# ============ LOCAL DATABASE VIEWS (for user uploads) ============

class LocalVideoListView(ListView):
    """List locally uploaded videos"""
    model = Video
    template_name = 'videos/local_videos.html'
    context_object_name = 'videos'
    paginate_by = 24

    def get_queryset(self):
        return Video.objects.filter(is_active=True).select_related('category', 'uploader')


class LocalVideoDetailView(DetailView):
    """Watch locally uploaded video"""
    model = Video
    template_name = 'videos/watch.html'
    context_object_name = 'video'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Video.objects.filter(is_active=True).select_related('category', 'uploader')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        ip = self.get_client_ip()
        if not VideoView.objects.filter(video=obj, ip_address=ip).exists():
            VideoView.objects.create(
                video=obj,
                ip_address=ip,
                user=self.request.user if self.request.user.is_authenticated else None
            )
            obj.views = F('views') + 1
            obj.save(update_fields=['views'])
            obj.refresh_from_db()
        return obj

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.object
        context['related_videos'] = Video.objects.filter(
            Q(category=video.category) | Q(tags__in=video.tags.all()),
            is_active=True
        ).exclude(pk=video.pk).distinct()[:12]
        context['comments'] = video.comments.filter(is_active=True).select_related('user')[:50]
        if self.request.user.is_authenticated:
            context['is_favorited'] = Favorite.objects.filter(user=self.request.user, video=video).exists()
            like_obj = VideoLike.objects.filter(user=self.request.user, video=video).first()
            context['user_like'] = like_obj.is_like if like_obj else None
        return context


@login_required
def like_video(request, slug):
    if request.method == 'POST':
        video = get_object_or_404(Video, slug=slug)
        like_obj, created = VideoLike.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={'is_like': True}
        )
        if not created:
            if like_obj.is_like:
                like_obj.delete()
                video.likes = F('likes') - 1
            else:
                like_obj.is_like = True
                like_obj.save()
                video.likes = F('likes') + 1
                video.dislikes = F('dislikes') - 1
        else:
            video.likes = F('likes') + 1
        video.save()
        video.refresh_from_db()
        return JsonResponse({'likes': video.likes, 'dislikes': video.dislikes})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def dislike_video(request, slug):
    if request.method == 'POST':
        video = get_object_or_404(Video, slug=slug)
        like_obj, created = VideoLike.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={'is_like': False}
        )
        if not created:
            if not like_obj.is_like:
                like_obj.delete()
                video.dislikes = F('dislikes') - 1
            else:
                like_obj.is_like = False
                like_obj.save()
                video.dislikes = F('dislikes') + 1
                video.likes = F('likes') - 1
        else:
            video.dislikes = F('dislikes') + 1
        video.save()
        video.refresh_from_db()
        return JsonResponse({'likes': video.likes, 'dislikes': video.dislikes})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def toggle_favorite(request, slug):
    if request.method == 'POST':
        video = get_object_or_404(Video, slug=slug)
        favorite, created = Favorite.objects.get_or_create(user=request.user, video=video)
        if not created:
            favorite.delete()
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def add_comment(request, slug):
    if request.method == 'POST':
        video = get_object_or_404(Video, slug=slug)
        content = request.POST.get('content', '').strip()
        if content:
            comment = Comment.objects.create(
                video=video,
                user=request.user,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'username': request.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%b %d, %Y')
            })
        return JsonResponse({'error': 'Content is required'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ============ PORNSTAR SECTION ============

def pornstars_view(request):
    """List all pornstars"""
    pornstars = PornstarService.get_all()
    return render(request, 'videos/pornstars/list.html', {'pornstars': pornstars})


def pornstar_detail_view(request, slug):
    """Pornstar profile with their videos"""
    pornstar = PornstarService.get_by_slug(slug)
    if not pornstar:
        return render(request, 'videos/error.html', {'message': 'Pornstar not found'})

    page = int(request.GET.get('page', 1))
    gay_param = get_user_gay_param(request)
    data = PornstarService.get_videos(pornstar['name'], page=page, per_page=24, gay=gay_param)
    total_count = int(data.get('total_count', 0)) if data else 0

    context = {
        'pornstar': pornstar,
        'videos': data.get('videos', []) if data else [],
        'total_count': total_count,
        'current_page': page,
        'has_next': page * 24 < total_count,
        'has_prev': page > 1,
    }
    return render(request, 'videos/pornstars/detail.html', context)


# ============ API VIDEO INTERACTIONS ============

@login_required
@require_POST
def api_video_like(request, video_id):
    """Like an API video"""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    source = data.get('source', 'eporner')

    like_obj, created = APIVideoLike.objects.get_or_create(
        user=request.user,
        video_id=video_id,
        source=source,
        defaults={'is_like': True}
    )

    if not created:
        if like_obj.is_like:
            # Already liked, remove the like
            like_obj.delete()
            status = 'removed'
        else:
            # Was dislike, change to like
            like_obj.is_like = True
            like_obj.save()
            status = 'liked'
    else:
        status = 'liked'

    # Get updated counts
    likes = APIVideoLike.objects.filter(video_id=video_id, source=source, is_like=True).count()
    dislikes = APIVideoLike.objects.filter(video_id=video_id, source=source, is_like=False).count()

    return JsonResponse({'status': status, 'likes': likes, 'dislikes': dislikes})


@login_required
@require_POST
def api_video_dislike(request, video_id):
    """Dislike an API video"""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    source = data.get('source', 'eporner')

    like_obj, created = APIVideoLike.objects.get_or_create(
        user=request.user,
        video_id=video_id,
        source=source,
        defaults={'is_like': False}
    )

    if not created:
        if not like_obj.is_like:
            # Already disliked, remove the dislike
            like_obj.delete()
            status = 'removed'
        else:
            # Was like, change to dislike
            like_obj.is_like = False
            like_obj.save()
            status = 'disliked'
    else:
        status = 'disliked'

    # Get updated counts
    likes = APIVideoLike.objects.filter(video_id=video_id, source=source, is_like=True).count()
    dislikes = APIVideoLike.objects.filter(video_id=video_id, source=source, is_like=False).count()

    return JsonResponse({'status': status, 'likes': likes, 'dislikes': dislikes})


@login_required
@require_POST
def api_video_favorite(request, video_id):
    """Toggle favorite for an API video"""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    source = data.get('source', 'eporner')
    title = data.get('title', '')
    thumbnail = data.get('thumbnail', '')
    duration = data.get('duration', '')

    favorite, created = APIVideoFavorite.objects.get_or_create(
        user=request.user,
        video_id=video_id,
        source=source,
        defaults={
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration
        }
    )

    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})

    return JsonResponse({'status': 'added'})


@login_required
@require_POST
def api_video_comment(request, video_id):
    """Add comment to an API video"""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    content = data.get('content', '').strip()
    source = data.get('source', 'eporner')

    if not content:
        return JsonResponse({'error': 'Comment content is required'}, status=400)

    comment = APIVideoComment.objects.create(
        user=request.user,
        video_id=video_id,
        source=source,
        content=content
    )

    return JsonResponse({
        'status': 'success',
        'comment': {
            'id': comment.id,
            'username': request.user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%b %d, %Y at %H:%M')
        }
    })


# ============ USER ACCOUNT PAGES ============

@login_required
def user_history(request):
    """User's watch history"""
    history = APIVideoView.objects.filter(user=request.user).order_by('-viewed_at')

    # Pagination
    page = int(request.GET.get('page', 1))
    paginator = Paginator(history, 24)
    page_obj = paginator.get_page(page)

    context = {
        'history': page_obj,
        'total_count': paginator.count,
        'current_page': page,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    }
    return render(request, 'videos/account/history.html', context)


@login_required
def user_favorites(request):
    """User's favorite videos"""
    favorites = APIVideoFavorite.objects.filter(user=request.user).order_by('-created_at')

    # Pagination
    page = int(request.GET.get('page', 1))
    paginator = Paginator(favorites, 24)
    page_obj = paginator.get_page(page)

    context = {
        'favorites': page_obj,
        'total_count': paginator.count,
        'current_page': page,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    }
    return render(request, 'videos/account/favorites.html', context)


@login_required
def user_liked_videos(request):
    """User's liked videos"""
    liked = APIVideoLike.objects.filter(user=request.user, is_like=True).order_by('-created_at')

    # We need to fetch video details for each liked video
    # For now, we'll just show the video IDs - could be enhanced to cache video info
    page = int(request.GET.get('page', 1))
    paginator = Paginator(liked, 24)
    page_obj = paginator.get_page(page)

    context = {
        'liked_videos': page_obj,
        'total_count': paginator.count,
        'current_page': page,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    }
    return render(request, 'videos/account/liked.html', context)


# ============ MAL-STYLE VIDEO LIST VIEWS ============

@login_required
def my_list_view(request):
    """User's video list (MAL-style)"""
    status_filter = request.GET.get('status', 'all')
    sort_by = request.GET.get('sort', '-updated_at')

    entries = VideoList.objects.filter(user=request.user)

    if status_filter != 'all':
        entries = entries.filter(status=status_filter)

    # Sorting options
    valid_sorts = ['-updated_at', 'updated_at', '-score', 'score', 'title', '-title', '-added_at']
    if sort_by in valid_sorts:
        entries = entries.order_by(sort_by)

    # Pagination
    page = int(request.GET.get('page', 1))
    paginator = Paginator(entries, 25)
    page_obj = paginator.get_page(page)

    # Get stats
    stats = VideoList.get_user_stats(request.user)

    context = {
        'entries': page_obj,
        'stats': stats,
        'current_status': status_filter,
        'current_sort': sort_by,
        'status_choices': VideoList.STATUS_CHOICES,
        'total_count': paginator.count,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    }
    return render(request, 'videos/account/my_list.html', context)


@login_required
@require_POST
def add_to_list(request):
    """Add video to user's list (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        source = data.get('source', 'eporner')
        title = data.get('title', '')
        thumbnail = data.get('thumbnail', '')
        duration = data.get('duration', '')
        status = data.get('status', 'plan_to_watch')

        if not video_id:
            return JsonResponse({'success': False, 'error': 'Video ID required'}, status=400)

        entry, created = VideoList.objects.update_or_create(
            user=request.user,
            video_id=video_id,
            source=source,
            defaults={
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'status': status,
            }
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'status': entry.status,
            'message': f'Added to {entry.get_status_display()}' if created else f'Updated to {entry.get_status_display()}'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_list_entry(request):
    """Update list entry status/score (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        source = data.get('source', 'eporner')

        entry = VideoList.objects.filter(
            user=request.user,
            video_id=video_id,
            source=source
        ).first()

        if not entry:
            return JsonResponse({'success': False, 'error': 'Entry not found'}, status=404)

        # Update fields if provided
        if 'status' in data:
            entry.status = data['status']
        if 'score' in data:
            score = data['score']
            entry.score = int(score) if score else None
        if 'notes' in data:
            entry.notes = data['notes']
        if 'times_watched' in data:
            entry.times_watched = int(data['times_watched'])

        entry.save()

        return JsonResponse({
            'success': True,
            'status': entry.status,
            'score': entry.score,
            'message': 'Entry updated'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def remove_from_list(request):
    """Remove video from user's list (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        source = data.get('source', 'eporner')

        deleted, _ = VideoList.objects.filter(
            user=request.user,
            video_id=video_id,
            source=source
        ).delete()

        return JsonResponse({
            'success': True,
            'deleted': deleted > 0,
            'message': 'Removed from list' if deleted else 'Entry not found'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_list_status(request, video_id):
    """Get user's list status for a video (AJAX)"""
    source = request.GET.get('source', 'eporner')

    entry = VideoList.objects.filter(
        user=request.user,
        video_id=video_id,
        source=source
    ).first()

    if entry:
        return JsonResponse({
            'in_list': True,
            'status': entry.status,
            'status_display': entry.get_status_display(),
            'score': entry.score,
            'times_watched': entry.times_watched,
            'notes': entry.notes,
        })

    return JsonResponse({'in_list': False})
