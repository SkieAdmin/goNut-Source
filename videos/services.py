import re
import requests
from urllib.parse import urlencode, quote_plus
from .cache import cached


class EpornerAPI:
    """
    EPORNER Free Public API
    Documentation: https://www.eporner.com/api/
    No API key required!
    """
    BASE_URL = "https://www.eporner.com/api/v2/video/search/"

    CATEGORIES = [
        'amateur', 'anal', 'asian', 'babe', 'bbw', 'big-tits', 'blonde',
        'blowjob', 'brunette', 'celebrity', 'ebony', 'fetish', 'hardcore',
        'latina', 'lesbian', 'milf', 'pornstar', 'pov', 'redhead', 'teen'
    ]

    @classmethod
    @cached(prefix='eporner:search', ttl=3600)  # 1 hour cache
    def search(cls, query="", page=1, per_page=24, order="latest", gay=0, lq=0):
        """
        Search for videos

        Args:
            query: Search term (optional)
            page: Page number (1-based)
            per_page: Results per page (max 1000)
            order: latest, longest, shortest, top-rated, most-popular, top-weekly, top-monthly
            gay: 0=straight, 1=gay, 2=both
            lq: 0=HD only, 1=include low quality
        """
        params = {
            'query': query,
            'per_page': per_page,
            'page': page,
            'thumbsize': 'big',  # small, medium, big
            'order': order,
            'gay': gay,
            'lq': lq,
            'format': 'json'
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return None

    @classmethod
    @cached(prefix='eporner:video_by_id', ttl=3600)  # 1 hour cache
    def get_video_by_id(cls, video_id):
        """Get single video details by ID"""
        url = f"https://www.eporner.com/api/v2/video/id/?id={video_id}&thumbsize=big&format=json"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return None

    @classmethod
    def get_by_category(cls, category, page=1, per_page=24, gay=0):
        """Get videos by category"""
        return cls.search(query=category, page=page, per_page=per_page, gay=gay)

    @classmethod
    def get_trending(cls, page=1, per_page=24, gay=0):
        """Get trending/popular videos"""
        return cls.search(page=page, per_page=per_page, order='top-weekly', gay=gay)

    @classmethod
    def get_latest(cls, page=1, per_page=24, gay=0):
        """Get latest videos"""
        return cls.search(page=page, per_page=per_page, order='latest', gay=gay)

    @classmethod
    @cached(prefix='eporner:top_rated', ttl=3600)  # 1 hour cache
    def get_top_rated(cls, page=1, per_page=24, gay=0):
        """Get top rated videos"""
        return cls.search(page=page, per_page=per_page, order='top-rated', gay=gay)


class HanimeAPI:
    """
    Hanime.tv API for Hentai content
    Using the search endpoint from htv-services.com
    """
    SEARCH_URL = "https://search.htv-services.com/"
    BASE_URL = "https://hanime.tv/api/v8"

    TAGS = [
        # Popular & Common
        'ahegao', 'anal', 'bdsm', 'big-boobs', 'blow-job', 'bondage', 'boob-job',
        'bukkake', 'creampie', 'facial', 'gangbang', 'harem', 'milf', 'pov',
        'threesome', 'uncensored', 'vanilla', 'virgin',

        # Character Types
        'animal-girls', 'cat-girl', 'demons', 'elf', 'furry', 'futanari',
        'gyaru', 'magical-girls', 'nekomimi', 'orc', 'succubus', 'vampire',

        # Occupations & Roles
        'doctor', 'female-doctor', 'female-teacher', 'housewife', 'maid',
        'nuns', 'nurse', 'office-ladies', 'police', 'princess', 'teacher',
        'school-girl', 'widow',

        # Family (Step)
        'step-daughter', 'step-mother', 'step-sister',

        # Actions & Fetishes
        'blackmail', 'brainwashed', 'cosplay', 'cross-dressing', 'dark-skin',
        'deep-throat', 'domination', 'double-penetration', 'facesitting',
        'femdom', 'foot-job', 'hand-job', 'humiliation', 'inflation',
        'internal-cumshot', 'lactation', 'masturbation', 'megane', 'glasses',
        'mind-break', 'mind-control', 'molestation', 'netorare', 'ntr',
        'orgy', 'pregnant', 'public-sex', 'rim-job', 'scat', 'shimapan',
        'shotacon', 'squirting', 'stockings', 'strap-on', 'tentacle',
        'tits-fuck', 'toys', 'train-molestation', 'trap', 'urination', 'x-ray',

        # Genres & Themes
        '3d', 'action', 'adventure', 'comedy', 'cute-funny', 'drama', 'dubbed',
        'ecchi', 'eroge', 'fantasy', 'historical', 'horror', 'martial-arts',
        'plot', 'romance', 'sci-fi', 'short', 'softcore', 'sports',
        'super-power', 'supernatural', 'tsundere',

        # Clothing & Accessories
        'condom', 'swimsuit',

        # Orientation
        'yaoi', 'yuri'
    ]

    @classmethod
    def _get_headers(cls):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://hanime.tv',
            'Referer': 'https://hanime.tv/',
        }

    @classmethod
    def _parse_videos(cls, hentai_videos):
        """Parse video list from API response"""
        import json
        videos = []

        # Handle case where hentai_videos is a JSON string
        if isinstance(hentai_videos, str):
            try:
                hentai_videos = json.loads(hentai_videos)
            except json.JSONDecodeError:
                return videos

        if not hentai_videos or not isinstance(hentai_videos, list):
            return videos

        for video in hentai_videos:
            if not isinstance(video, dict):
                continue

            # Convert duration from ms to minutes:seconds format
            duration_ms = video.get('duration_in_ms', 0)
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) // 1000
            duration_str = f"{minutes}:{seconds:02d}"

            videos.append({
                'id': video.get('id'),
                'slug': video.get('slug', ''),
                'title': video.get('name', 'Unknown'),
                'cover_url': video.get('cover_url', ''),
                'poster_url': video.get('poster_url', ''),
                'views': video.get('views', 0),
                'likes': video.get('likes', 0),
                'monthly_rank': video.get('monthly_rank'),
                'brand': video.get('brand', ''),
                'duration_in_ms': duration_ms,
                'duration': duration_str,
                'released_at': video.get('released_at', ''),
                'tags': video.get('tags', []),
                'is_censored': video.get('is_censored', True)
            })
        return videos

    @classmethod
    def search(cls, query="", page=0, tags=None, brands=None, order_by="created_at", ordering="desc"):
        """
        Search for hentai videos using search.htv-services.com
        """
        payload = {
            'search_text': query,
            'tags': tags or [],
            'tags_mode': 'AND',
            'brands': brands or [],
            'blacklist': [],
            'order_by': order_by,
            'ordering': ordering,
            'page': page
        }

        try:
            response = requests.post(cls.SEARCH_URL, headers=cls._get_headers(), json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            # The 'hits' field is a JSON string that needs to be parsed
            videos = cls._parse_videos(data.get('hits', '[]'))
            total_count = data.get('nbHits', 0)
            total_pages = data.get('nbPages', 0)

            return {
                'videos': videos,
                'total_count': total_count,
                'page': page,
                'pages': total_pages
            }
        except Exception as e:
            print(f"Hanime API Error: {e}")
            return {'videos': [], 'total_count': 0, 'page': 0, 'pages': 0}

    @classmethod
    def get_video_by_slug(cls, slug):
        """Get single video details by slug"""
        url = f"{cls.BASE_URL}/video?id={slug}"

        try:
            response = requests.get(url, headers=cls._get_headers(), timeout=15)
            response.raise_for_status()
            data = response.json()

            hentai_video = data.get('hentai_video', {})
            if not hentai_video:
                return None

            return {
                'id': hentai_video.get('id'),
                'slug': hentai_video.get('slug'),
                'title': hentai_video.get('name', ''),
                'description': hentai_video.get('description', ''),
                'cover_url': hentai_video.get('cover_url', ''),
                'poster_url': hentai_video.get('poster_url', ''),
                'views': hentai_video.get('views', 0),
                'likes': hentai_video.get('likes', 0),
                'dislikes': hentai_video.get('dislikes', 0),
                'brand': hentai_video.get('brand', ''),
                'duration_in_ms': hentai_video.get('duration_in_ms', 0),
                'released_at': hentai_video.get('released_at', ''),
                'tags': [t.get('text', '') for t in hentai_video.get('hentai_tags', [])] if hentai_video.get('hentai_tags') else [],
                'is_censored': hentai_video.get('is_censored', True),
                'streams': data.get('videos_manifest', {}).get('servers', []) if data.get('videos_manifest') else [],
                'episodes': data.get('hentai_franchise_hentai_videos', [])
            }
        except Exception as e:
            print(f"Hanime API Error: {e}")
            return None

    @classmethod
    def get_trending(cls, page=0, period="month"):
        """Get trending hentai videos (sorted by views)"""
        return cls.search(page=page, order_by='views', ordering='desc')

    @classmethod
    def get_latest(cls, page=0):
        """Get latest hentai releases"""
        return cls.search(page=page, order_by='created_at', ordering='desc')

    @classmethod
    def get_by_tag(cls, tag, page=0):
        """Get videos by tag"""
        return cls.search(tags=[tag], page=page, order_by='views', ordering='desc')


class EpornerHentaiAPI:
    """
    Alternative Hentai source using Eporner's hentai category
    Use this as a backup if Hanime.tv is not working
    """

    @classmethod
    def search(cls, query="hentai", page=1, per_page=24, gay=0):
        """Search for hentai videos on Eporner"""
        search_query = f"hentai {query}" if query and query != "hentai" else "hentai"
        return EpornerAPI.search(query=search_query, page=page, per_page=per_page, gay=gay)

    @classmethod
    def get_trending(cls, page=1, per_page=24):
        """Get trending hentai from Eporner"""
        return EpornerAPI.search(query="hentai", page=page, per_page=per_page, order='top-weekly')

    @classmethod
    def get_latest(cls, page=1, per_page=24):
        """Get latest hentai from Eporner"""
        return EpornerAPI.search(query="hentai", page=page, per_page=per_page, order='latest')


class RedTubeAPI:
    """
    RedTube Public API with automatic fallback to Eporner
    Documentation: https://api.redtube.com/
    No API key required!

    Note: RedTube API has a daily limit of 30,000 queries.
    When limit is reached, automatically falls back to Eporner API.
    Cache TTL is set to 12 hours to minimize API calls.
    """
    BASE_URL = "https://api.redtube.com/"
    _rate_limited = False  # Track if we're rate limited today
    _rate_limit_date = None  # Track when rate limit was hit

    # Cache TTL: 12 hours = 43200 seconds
    CACHE_TTL = 43200

    @classmethod
    def _check_rate_limit_reset(cls):
        """Reset rate limit flag if it's a new day"""
        from datetime import date
        today = date.today()
        if cls._rate_limit_date and cls._rate_limit_date != today:
            print("[RedTube API] New day - resetting rate limit flag")
            cls._rate_limited = False
            cls._rate_limit_date = None

    @classmethod
    def _fallback_to_eporner(cls, query="", page=1, ordering="newest"):
        """Fallback to Eporner API when RedTube is rate limited"""
        print("[RedTube API] Rate limited - falling back to Eporner API")

        # Map RedTube ordering to Eporner ordering
        order_map = {
            'newest': 'latest',
            'mostviewed': 'most-popular',
            'rating': 'top-rated',
        }
        eporner_order = order_map.get(ordering, 'latest')

        # Get results from Eporner
        eporner_result = EpornerAPI.search(query=query, page=page, order=eporner_order, per_page=20)

        if not eporner_result or 'videos' not in eporner_result:
            return {'videos': [], 'count': 0, 'fallback': True}

        # Convert Eporner format to RedTube-like format for consistency
        normalized = []
        for video in eporner_result.get('videos', []):
            # Get the best thumbnail
            thumbs = video.get('thumbs', [])
            thumb_url = thumbs[0].get('src', '') if thumbs else video.get('default_thumb', {}).get('src', '')

            normalized.append({
                'id': video.get('id'),
                'title': video.get('title', ''),
                'url': video.get('url', ''),
                'thumb': thumb_url,
                'thumbs': thumbs,
                'publish_date': video.get('added', ''),
                'duration': video.get('length_min', ''),
                'views': video.get('views', 0),
                'rating': float(video.get('rate', 0)),
                'ratings': 0,
                'tags': video.get('keywords', '').split(',') if video.get('keywords') else [],
                'pornstars': [],
            })

        return {
            'videos': normalized,
            'count': eporner_result.get('total_count', len(normalized)),
            'fallback': True  # Flag to indicate this is fallback data
        }

    @classmethod
    @cached(prefix='redtube:search', ttl=43200)  # 12 hours cache
    def search(cls, query="", category="", tags="", stars="", page=1, ordering="newest", period="alltime"):
        """
        Search for videos

        Args:
            query: Search term
            category: Category name
            tags: Comma-separated tags
            stars: Pornstar name
            page: Page number (20 results per page)
            ordering: newest, mostviewed, rating
            period: weekly, monthly, alltime
        """
        # Check if rate limit should be reset (new day)
        cls._check_rate_limit_reset()

        # If we know we're rate limited, go straight to fallback
        if cls._rate_limited:
            return cls._fallback_to_eporner(query, page, ordering)

        params = {
            'data': 'redtube.Videos.searchVideos',
            'output': 'json',
            'search': query,
            'category': category,
            'tags[]': tags,
            'stars[]': stars,
            'page': page,
            'ordering': ordering,
            'period': period,
            'thumbsize': 'big'
        }

        # Remove empty params
        params = {k: v for k, v in params.items() if v}

        try:
            # Add headers to appear more like a browser (helps avoid IP blocking)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.redtube.com/',
            }
            response = requests.get(cls.BASE_URL, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Check for rate limit error (code 1005)
            if data.get('code') == 1005 or 'limit' in data.get('message', '').lower():
                from datetime import date
                print(f"[RedTube API] Rate limit reached: {data.get('message')}")
                cls._rate_limited = True
                cls._rate_limit_date = date.today()
                return cls._fallback_to_eporner(query, page, ordering)

            videos = data.get('videos', [])
            print(f"[RedTube API] Found {len(videos)} videos")

            # Normalize video structure
            normalized = []
            for v in videos:
                video = v.get('video', v)
                normalized.append({
                    'id': video.get('video_id'),
                    'title': video.get('title', ''),
                    'url': video.get('url', ''),
                    'thumb': video.get('thumb', video.get('default_thumb', '')),
                    'thumbs': video.get('thumbs', []),
                    'publish_date': video.get('publish_date', ''),
                    'duration': video.get('duration', ''),
                    'views': video.get('views', 0),
                    'rating': video.get('rating', 0),
                    'ratings': video.get('ratings', 0),
                    'tags': video.get('tags', []),
                    'pornstars': video.get('pornstars', []),
                })

            return {
                'videos': normalized,
                'count': int(data.get('count', len(normalized))),
                'fallback': False
            }
        except requests.RequestException as e:
            print(f"[RedTube API Error] {e}")
            # On network errors, try fallback
            return cls._fallback_to_eporner(query, page, ordering)
        except Exception as e:
            print(f"[RedTube API Exception] {e}")
            return cls._fallback_to_eporner(query, page, ordering)

    @classmethod
    @cached(prefix='redtube:video_by_id', ttl=43200)  # 12 hours cache
    def get_video_by_id(cls, video_id):
        """Get single video details by ID"""
        params = {
            'data': 'redtube.Videos.getVideoById',
            'output': 'json',
            'video_id': video_id,
            'thumbsize': 'big'
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            videos = data.get('videos', [])
            if videos:
                video = videos[0].get('video', videos[0])
                return {
                    'id': video.get('video_id'),
                    'title': video.get('title', ''),
                    'url': video.get('url', ''),
                    'embed_url': video.get('embed_url', ''),
                    'thumb': video.get('thumb', ''),
                    'thumbs': video.get('thumbs', []),
                    'publish_date': video.get('publish_date', ''),
                    'duration': video.get('duration', ''),
                    'views': video.get('views', 0),
                    'rating': video.get('rating', 0),
                    'tags': video.get('tags', []),
                    'pornstars': video.get('pornstars', []),
                }
            return None
        except requests.RequestException as e:
            print(f"RedTube API Error: {e}")
            return None

    @classmethod
    def get_embed_code(cls, video_id):
        """Get embed code for a video"""
        params = {
            'data': 'redtube.Videos.getVideoEmbedCode',
            'output': 'json',
            'video_id': video_id
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            embed = data.get('embed', {})
            return embed.get('code', '')
        except requests.RequestException as e:
            print(f"RedTube API Error: {e}")
            return None

    @classmethod
    def get_categories(cls):
        """Get all available categories"""
        params = {
            'data': 'redtube.Categories.getCategoriesList',
            'output': 'json'
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get('categories', [])
        except requests.RequestException as e:
            print(f"RedTube API Error: {e}")
            return []

    @classmethod
    def get_trending(cls, page=1):
        """Get most viewed videos this week"""
        return cls.search(page=page, ordering='mostviewed', period='weekly')

    @classmethod
    def get_latest(cls, page=1):
        """Get newest videos"""
        return cls.search(page=page, ordering='newest')

    @classmethod
    def get_top_rated(cls, page=1):
        """Get top rated videos"""
        return cls.search(page=page, ordering='rating')


class XVideosAPI:
    """
    xVideos Scraper API
    No official API - uses web scraping with predictable URL patterns
    """
    BASE_URL = "https://www.xvideos.com"

    CATEGORIES = [
        'amateur', 'anal', 'asian', 'babe', 'bbw', 'big-tits', 'blonde',
        'blowjob', 'brunette', 'creampie', 'ebony', 'hardcore', 'hd-videos',
        'latina', 'lesbian', 'milf', 'pornstar', 'pov', 'redhead', 'teen'
    ]

    @classmethod
    def _get_headers(cls):
        """Get browser-like headers to avoid blocking"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    @classmethod
    def _parse_duration(cls, duration_str):
        """Parse duration string like '10 min' or '1h 30 min' to formatted string"""
        if not duration_str:
            return '0:00'
        duration_str = duration_str.strip().lower()

        # Handle formats like "10 min", "1h 30 min", "5min"
        hours = 0
        minutes = 0

        h_match = re.search(r'(\d+)\s*h', duration_str)
        m_match = re.search(r'(\d+)\s*min', duration_str)

        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))

        if hours:
            return f"{hours}:{minutes:02d}:00"
        return f"{minutes}:00"

    @classmethod
    def _parse_views(cls, views_str):
        """Parse views string like '1.2M' or '500k' to integer"""
        if not views_str:
            return 0
        views_str = views_str.strip().upper().replace(' ', '').replace('VIEWS', '')

        try:
            if 'M' in views_str:
                return int(float(views_str.replace('M', '')) * 1000000)
            elif 'K' in views_str:
                return int(float(views_str.replace('K', '')) * 1000)
            else:
                return int(views_str.replace(',', ''))
        except (ValueError, AttributeError):
            return 0

    @classmethod
    def _extract_videos_from_html(cls, html):
        """Extract video data from HTML using regex"""
        videos = []

        # Pattern to match video thumb blocks
        # xVideos uses a specific HTML structure for video thumbnails
        thumb_pattern = re.compile(
            r'<div[^>]*class="[^"]*thumb-block[^"]*"[^>]*>.*?'
            r'<a[^>]*href="(/video[^"]+)"[^>]*>.*?'
            r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*>.*?'
            r'<p[^>]*class="[^"]*title[^"]*"[^>]*><a[^>]*>([^<]+)</a>.*?'
            r'(?:<span[^>]*class="[^"]*duration[^"]*"[^>]*>([^<]*)</span>)?',
            re.DOTALL | re.IGNORECASE
        )

        # Alternative simpler pattern
        video_pattern = re.compile(
            r'<div[^>]*id="video_(\d+)"[^>]*>.*?'
            r'<a[^>]*href="(/video[^"]+)"[^>]*title="([^"]*)"[^>]*>.*?'
            r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*>.*?'
            r'(?:<span[^>]*class="duration"[^>]*>([^<]*)</span>)?',
            re.DOTALL | re.IGNORECASE
        )

        matches = video_pattern.findall(html)

        if not matches:
            # Try another pattern for search results
            alt_pattern = re.compile(
                r'<div[^>]*class="thumb"[^>]*>.*?'
                r'<a[^>]*href="(/video[^"]+)"[^>]*>.*?'
                r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?'
                r'<span[^>]*class="duration"[^>]*>([^<]*)</span>',
                re.DOTALL | re.IGNORECASE
            )
            alt_matches = alt_pattern.findall(html)

            for url, thumb, title, duration in alt_matches:
                video_id = url.split('/')[-1].split('_')[0] if '/' in url else url
                videos.append({
                    'id': video_id,
                    'title': title.strip() if title else 'Unknown',
                    'url': f"{cls.BASE_URL}{url}",
                    'thumb': thumb if thumb.startswith('http') else f"https:{thumb}",
                    'duration': cls._parse_duration(duration),
                    'views': 0,
                    'rating': 0,
                })
        else:
            for video_id, url, title, thumb, duration in matches:
                videos.append({
                    'id': video_id,
                    'title': title.strip() if title else 'Unknown',
                    'url': f"{cls.BASE_URL}{url}",
                    'thumb': thumb if thumb.startswith('http') else f"https:{thumb}",
                    'duration': cls._parse_duration(duration),
                    'views': 0,
                    'rating': 0,
                })

        return videos

    @classmethod
    @cached(prefix='xvideos:search', ttl=3600)  # 1 hour cache
    def search(cls, query="", page=0, sort="relevance"):
        """
        Search for videos on xVideos

        Args:
            query: Search term
            page: Page number (0-based)
            sort: relevance, uploaddate, rating, length, views
        """
        try:
            if query:
                # Search URL format: /search/query/page
                search_query = quote_plus(query)
                url = f"{cls.BASE_URL}/?k={search_query}&p={page}"
            else:
                # Default to homepage or best videos
                url = f"{cls.BASE_URL}/best/{page}" if page > 0 else f"{cls.BASE_URL}/best"

            print(f"[xVideos] Fetching: {url}")
            response = requests.get(url, headers=cls._get_headers(), timeout=15)
            response.raise_for_status()

            html = response.text
            videos = cls._extract_videos_from_html(html)

            print(f"[xVideos] Found {len(videos)} videos")

            return {
                'videos': videos,
                'count': len(videos),
                'page': page,
            }
        except requests.RequestException as e:
            print(f"[xVideos Error] {e}")
            return {'videos': [], 'count': 0, 'page': page}
        except Exception as e:
            print(f"[xVideos Exception] {e}")
            return {'videos': [], 'count': 0, 'page': page}

    @classmethod
    @cached(prefix='xvideos:video', ttl=3600)  # 1 hour cache
    def get_video_by_id(cls, video_url):
        """Get video details by URL or ID"""
        try:
            # Handle both full URL and partial
            if not video_url.startswith('http'):
                url = f"{cls.BASE_URL}{video_url}" if video_url.startswith('/') else f"{cls.BASE_URL}/video{video_url}"
            else:
                url = video_url

            response = requests.get(url, headers=cls._get_headers(), timeout=15)
            response.raise_for_status()

            html = response.text

            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', html)
            title = title_match.group(1).replace(' - XVIDEOS.COM', '').strip() if title_match else 'Unknown'

            # Extract thumbnail
            thumb_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
            thumb = thumb_match.group(1) if thumb_match else ''

            # Extract duration
            duration_match = re.search(r'"duration":\s*"?(\d+)"?', html)
            duration_seconds = int(duration_match.group(1)) if duration_match else 0
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration = f"{minutes}:{seconds:02d}"

            # Extract video ID from URL
            id_match = re.search(r'/video(\d+)/', url)
            video_id = id_match.group(1) if id_match else url.split('/')[-1]

            # Extract embed URL
            embed_url = f"{cls.BASE_URL}/embedframe/{video_id}"

            return {
                'id': video_id,
                'title': title,
                'url': url,
                'embed_url': embed_url,
                'thumb': thumb,
                'duration': duration,
                'views': 0,
                'rating': 0,
            }
        except Exception as e:
            print(f"[xVideos Error] get_video_by_id: {e}")
            return None

    @classmethod
    def get_trending(cls, page=0):
        """Get trending/best videos"""
        return cls.search(page=page)

    @classmethod
    @cached(prefix='xvideos:latest', ttl=1800)  # 30 min cache
    def get_latest(cls, page=0):
        """Get newest videos"""
        try:
            url = f"{cls.BASE_URL}/new/{page}" if page > 0 else f"{cls.BASE_URL}/new"

            response = requests.get(url, headers=cls._get_headers(), timeout=15)
            response.raise_for_status()

            videos = cls._extract_videos_from_html(response.text)

            return {
                'videos': videos,
                'count': len(videos),
                'page': page,
            }
        except Exception as e:
            print(f"[xVideos Error] get_latest: {e}")
            return {'videos': [], 'count': 0, 'page': page}

    @classmethod
    @cached(prefix='xvideos:category', ttl=3600)  # 1 hour cache
    def get_by_category(cls, category, page=0):
        """Get videos by category"""
        try:
            url = f"{cls.BASE_URL}/c/{category}/{page}" if page > 0 else f"{cls.BASE_URL}/c/{category}"

            response = requests.get(url, headers=cls._get_headers(), timeout=15)
            response.raise_for_status()

            videos = cls._extract_videos_from_html(response.text)

            return {
                'videos': videos,
                'count': len(videos),
                'page': page,
            }
        except Exception as e:
            print(f"[xVideos Error] get_by_category: {e}")
            return {'videos': [], 'count': 0, 'page': page}

    @classmethod
    def get_embed_url(cls, video_id):
        """Get embed URL for a video"""
        return f"{cls.BASE_URL}/embedframe/{video_id}"


def parse_duration(length_sec):
    """Convert seconds string to integer"""
    try:
        return int(length_sec)
    except (ValueError, TypeError):
        return 0


def get_embed_url(video_id):
    """Get embeddable video URL"""
    return f"https://www.eporner.com/embed/{video_id}/"


def get_quality_label(keywords):
    """Determine video quality from keywords"""
    keywords_lower = keywords.lower() if keywords else ""
    if '4k' in keywords_lower or '2160p' in keywords_lower:
        return '4k'
    elif '1080p' in keywords_lower or 'full hd' in keywords_lower:
        return '1080p'
    elif '720p' in keywords_lower or 'hd' in keywords_lower:
        return '720p'
    elif '480p' in keywords_lower:
        return '480p'
    return '720p'


class PornstarService:
    """
    Pornstar data service with curated list of popular adult performers
    Uses Eporner API for video search by performer name
    """

    # Popular pornstars with profile images (using placeholder avatars)
    PORNSTARS = [
        {'name': 'Riley Reid', 'slug': 'riley-reid', 'gender': 'female'},
        {'name': 'Mia Khalifa', 'slug': 'mia-khalifa', 'gender': 'female'},
        {'name': 'Lana Rhoades', 'slug': 'lana-rhoades', 'gender': 'female'},
        {'name': 'Abella Danger', 'slug': 'abella-danger', 'gender': 'female'},
        {'name': 'Angela White', 'slug': 'angela-white', 'gender': 'female'},
        {'name': 'Eva Elfie', 'slug': 'eva-elfie', 'gender': 'female'},
        {'name': 'Emily Willis', 'slug': 'emily-willis', 'gender': 'female'},
        {'name': 'Elsa Jean', 'slug': 'elsa-jean', 'gender': 'female'},
        {'name': 'Gabbie Carter', 'slug': 'gabbie-carter', 'gender': 'female'},
        {'name': 'Mia Malkova', 'slug': 'mia-malkova', 'gender': 'female'},
        {'name': 'Adriana Chechik', 'slug': 'adriana-chechik', 'gender': 'female'},
        {'name': 'Lexi Luna', 'slug': 'lexi-luna', 'gender': 'female'},
        {'name': 'Brandi Love', 'slug': 'brandi-love', 'gender': 'female'},
        {'name': 'Nicole Aniston', 'slug': 'nicole-aniston', 'gender': 'female'},
        {'name': 'Madison Ivy', 'slug': 'madison-ivy', 'gender': 'female'},
        {'name': 'Kendra Lust', 'slug': 'kendra-lust', 'gender': 'female'},
        {'name': 'Lisa Ann', 'slug': 'lisa-ann', 'gender': 'female'},
        {'name': 'Asa Akira', 'slug': 'asa-akira', 'gender': 'female'},
        {'name': 'Dani Daniels', 'slug': 'dani-daniels', 'gender': 'female'},
        {'name': 'Kenzie Reeves', 'slug': 'kenzie-reeves', 'gender': 'female'},
        {'name': 'Autumn Falls', 'slug': 'autumn-falls', 'gender': 'female'},
        {'name': 'Violet Myers', 'slug': 'violet-myers', 'gender': 'female'},
        {'name': 'Skylar Vox', 'slug': 'skylar-vox', 'gender': 'female'},
        {'name': 'Lily Larimar', 'slug': 'lily-larimar', 'gender': 'female'},
        {'name': 'Vina Sky', 'slug': 'vina-sky', 'gender': 'female'},
        {'name': 'Cory Chase', 'slug': 'cory-chase', 'gender': 'female'},
        {'name': 'Alexis Texas', 'slug': 'alexis-texas', 'gender': 'female'},
        {'name': 'Jynx Maze', 'slug': 'jynx-maze', 'gender': 'female'},
        {'name': 'Johnny Sins', 'slug': 'johnny-sins', 'gender': 'male'},
        {'name': 'Jordi El Nino', 'slug': 'jordi-el-nino', 'gender': 'male'},
        {'name': 'Manuel Ferrara', 'slug': 'manuel-ferrara', 'gender': 'male'},
        {'name': 'Keiran Lee', 'slug': 'keiran-lee', 'gender': 'male'},
        {'name': 'Xander Corvus', 'slug': 'xander-corvus', 'gender': 'male'},
        {'name': 'Markus Dupree', 'slug': 'markus-dupree', 'gender': 'male'},
    ]

    @classmethod
    @cached(prefix='pornstar:all', ttl=43200)  # 12 hours cache
    def get_all(cls):
        """Get all pornstars with avatar URLs"""
        stars = []
        for star in cls.PORNSTARS:
            stars.append({
                **star,
                'avatar': cls._get_avatar_url(star['name']),
            })
        return stars

    @classmethod
    def get_popular(cls, limit=20):
        """Get popular pornstars"""
        return cls.get_all()[:limit]

    @classmethod
    def get_by_slug(cls, slug):
        """Get pornstar by slug"""
        for star in cls.PORNSTARS:
            if star['slug'] == slug:
                return {
                    **star,
                    'avatar': cls._get_avatar_url(star['name']),
                }
        return None

    @classmethod
    @cached(prefix='pornstar:videos', ttl=3600)  # 1 hour cache
    def get_videos(cls, name, page=1, per_page=24, gay=0):
        """Get videos featuring a pornstar"""
        return EpornerAPI.search(query=name, page=page, per_page=per_page, gay=gay, order='most-popular')

    @classmethod
    def _get_avatar_url(cls, name):
        """Generate avatar URL using UI Avatars service"""
        # Using ui-avatars.com for placeholder avatars
        initials = ''.join([n[0] for n in name.split()[:2]])
        colors = ['9333ea', 'ec4899', 'f43f5e', '8b5cf6', '6366f1', '3b82f6']
        color = colors[hash(name) % len(colors)]
        return f"https://ui-avatars.com/api/?name={initials}&background={color}&color=fff&size=200&bold=true"

    @classmethod
    def search(cls, query):
        """Search pornstars by name"""
        query_lower = query.lower()
        results = []
        for star in cls.PORNSTARS:
            if query_lower in star['name'].lower():
                results.append({
                    **star,
                    'avatar': cls._get_avatar_url(star['name']),
                })
        return results
