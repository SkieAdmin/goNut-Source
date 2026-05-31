from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.static import serve as media_serve

from .sitemaps import StaticViewSitemap, CategorySitemap

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
}


def robots_txt(request):
    """Generate robots.txt for SEO"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Disallow admin and account pages",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "",
        "# Disallow API endpoints",
        "Disallow: /*?",
        "",
        "# Sitemap",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
        "",
        "# Crawl-delay",
        "Crawl-delay: 1",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', cache_page(86400)(sitemap), {'sitemaps': sitemaps}, name='sitemap'),
    path('', include('videos.urls')),
    path('accounts/', include('accounts.urls')),
]

# Serve user-uploaded media. There is no separate web server configured for
# this project, so Django serves /media/ in production too (WhiteNoise handles
# /static/ via middleware). If you later put nginx/CDN in front, drop this.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
