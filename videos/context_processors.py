from .models import Category


def categories_processor(request):
    return {
        'nav_categories': Category.objects.all()[:10]
    }
