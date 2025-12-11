"""
SEO Context Processor - Provides site-wide SEO data to all templates
"""
from django.conf import settings


def seo_processor(request):
    """
    Adds SEO-related variables to the template context.
    These can be used across all templates for consistent SEO implementation.
    """
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'goNuts'),
        'site_domain': getattr(settings, 'SITE_DOMAIN', 'gonut.click'),
        'site_url': getattr(settings, 'SITE_URL', 'https://gonut.click'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', 'Your Ultimate Adult Entertainment Universe'),
        'site_description': getattr(settings, 'SITE_DESCRIPTION', ''),
        'site_keywords': ', '.join(getattr(settings, 'SITE_KEYWORDS', [])),
        'social_links': getattr(settings, 'SOCIAL_LINKS', {}),
        'seo_default_image': getattr(settings, 'SEO_DEFAULT_IMAGE', ''),
        'seo_twitter_handle': getattr(settings, 'SEO_TWITTER_HANDLE', ''),
        'canonical_url': request.build_absolute_uri(request.path),
    }
