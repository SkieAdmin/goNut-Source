from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    # API-powered views (main site)
    path('', views.home_view, name='home'),
    path('watch/<str:video_id>/', views.watch_view, name='watch'),
    path('categories/', views.category_list_view, name='categories'),
    path('category/<slug:slug>/', views.category_detail_view, name='category'),
    path('search/', views.search_view, name='search'),
    path('trending/', views.trending_view, name='trending'),
    path('newest/', views.newest_view, name='newest'),
    path('top-rated/', views.top_rated_view, name='top_rated'),

    # Hentai section (Hanime.tv API)
    path('hentai/', views.hentai_home_view, name='hentai_home'),
    path('hentai/browse/', views.hentai_browse_view, name='hentai_browse'),
    path('hentai/trending/', views.hentai_trending_view, name='hentai_trending'),
    path('hentai/newest/', views.hentai_newest_view, name='hentai_newest'),
    path('hentai/watch/<slug:slug>/', views.hentai_watch_view, name='hentai_watch'),
    path('hentai/tags/', views.hentai_tags_view, name='hentai_tags'),
    path('hentai/tag/<slug:tag>/', views.hentai_tag_view, name='hentai_tag'),
    path('hentai/search/', views.hentai_search_view, name='hentai_search'),

    # RedTube section
    path('redtube/', views.redtube_home_view, name='redtube_home'),
    path('redtube/browse/', views.redtube_browse_view, name='redtube_browse'),
    path('redtube/watch/<str:video_id>/', views.redtube_watch_view, name='redtube_watch'),
    path('redtube/search/', views.redtube_search_view, name='redtube_search'),

    # xVideos section
    path('xvideos/watch/<str:video_id>/', views.xvideos_watch_view, name='xvideos_watch'),

    # Pornstars section
    path('pornstars/', views.pornstars_view, name='pornstars'),
    path('pornstar/<slug:slug>/', views.pornstar_detail_view, name='pornstar_detail'),

    # Local uploads (for your own videos)
    path('local/', views.LocalVideoListView.as_view(), name='local_videos'),
    path('local/<slug:slug>/', views.LocalVideoDetailView.as_view(), name='local_watch'),

    # Interactions (for local videos)
    path('like/<slug:slug>/', views.like_video, name='like'),
    path('dislike/<slug:slug>/', views.dislike_video, name='dislike'),
    path('favorite/<slug:slug>/', views.toggle_favorite, name='favorite'),
    path('comment/<slug:slug>/', views.add_comment, name='comment'),

    # API Video Interactions (for external API videos)
    path('api/video/<str:video_id>/like/', views.api_video_like, name='api_video_like'),
    path('api/video/<str:video_id>/dislike/', views.api_video_dislike, name='api_video_dislike'),
    path('api/video/<str:video_id>/favorite/', views.api_video_favorite, name='api_video_favorite'),
    path('api/video/<str:video_id>/comment/', views.api_video_comment, name='api_video_comment'),

    # User Account Pages
    path('account/history/', views.user_history, name='user_history'),
    path('account/favorites/', views.user_favorites, name='user_favorites'),
    path('account/liked/', views.user_liked_videos, name='user_liked'),

    # MAL-Style Video List
    path('mylist/', views.my_list_view, name='my_list'),
    path('api/list/add/', views.add_to_list, name='add_to_list'),
    path('api/list/update/', views.update_list_entry, name='update_list_entry'),
    path('api/list/remove/', views.remove_from_list, name='remove_from_list'),
    path('api/list/status/<str:video_id>/', views.get_list_status, name='get_list_status'),

    # User Video Upload
    path('upload/', views.upload_video_view, name='upload'),
    path('my-videos/', views.my_videos_view, name='my_videos'),
    path('edit/<slug:slug>/', views.edit_video_view, name='edit_video'),
    path('delete/<slug:slug>/', views.delete_video_view, name='delete_video'),
]
