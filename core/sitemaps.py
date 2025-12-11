"""
Sitemap configuration for SEO
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return [
            'videos:home',
            'videos:trending',
            'videos:newest',
            'videos:categories',
            'videos:hentai_home',
            'videos:redtube_home',
            'videos:pornstars',
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    """Sitemap for category pages"""
    priority = 0.7
    changefreq = 'daily'

    def items(self):
        # Common categories - these are hardcoded to avoid DB dependency
        categories = [
            'amateur', 'asian', 'milf', 'teen', 'latina', 'lesbian',
            'blonde', 'brunette', 'ebony', 'anal', 'big-tits', 'blowjob',
            'hardcore', 'pornstar', 'pov', 'threesome', 'interracial'
        ]
        return categories

    def location(self, item):
        return reverse('videos:category', kwargs={'slug': item})
