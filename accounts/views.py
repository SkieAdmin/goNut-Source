from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from videos.models import Favorite, Playlist, APIVideoView, APIVideoFavorite, APIVideoLike, VideoList
from .forms import CustomUserCreationForm, ProfileUpdateForm, UserUpdateForm, CustomPasswordChangeForm
from .models import UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('videos:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('videos:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('videos:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                # Handle "Remember Me" checkbox
                if request.POST.get('remember_me'):
                    # Keep session for 30 days
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    # Session expires when browser closes
                    request.session.set_expiry(0)

                next_url = request.GET.get('next', 'videos:home')
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('videos:home')


@login_required
def profile_view(request):
    # Get API video data (from external APIs like Eporner, RedTube)
    recent_views = APIVideoView.objects.filter(user=request.user).order_by('-viewed_at')[:6]
    api_favorites = APIVideoFavorite.objects.filter(user=request.user).order_by('-created_at')[:6]
    api_likes = APIVideoLike.objects.filter(user=request.user, is_like=True).count()

    # MAL-style list data
    list_stats = VideoList.get_user_stats(request.user)
    recent_list_entries = VideoList.objects.filter(user=request.user).order_by('-updated_at')[:6]

    # Legacy local video data
    local_favorites = Favorite.objects.filter(user=request.user).select_related('video')[:6]
    playlists = Playlist.objects.filter(user=request.user)

    context = {
        'recent_views': recent_views,
        'api_favorites': api_favorites,
        'api_likes_count': api_likes,
        'list_stats': list_stats,
        'recent_list_entries': recent_list_entries,
        'local_favorites': local_favorites,
        'playlists': playlists,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('video')
    return render(request, 'accounts/favorites.html', {'favorites': favorites})


@login_required
def edit_profile_view(request):
    """Edit user profile - avatar, gender, preference"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password_view(request):
    """Change user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password has been changed!')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


def public_profile_view(request, username):
    """View a user's public profile"""
    profile_user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=profile_user)

    # Get list stats if user allows it
    list_stats = None
    recent_list_entries = []
    if profile.show_stats:
        list_stats = VideoList.get_user_stats(profile_user)
        if profile.list_is_public:
            recent_list_entries = VideoList.objects.filter(user=profile_user).order_by('-updated_at')[:6]

    # Get favorites if user allows it
    recent_favorites = []
    if profile.show_favorites:
        recent_favorites = APIVideoFavorite.objects.filter(user=profile_user).order_by('-created_at')[:6]

    # Check if viewing own profile
    is_own_profile = request.user == profile_user

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'list_stats': list_stats,
        'recent_list_entries': recent_list_entries,
        'recent_favorites': recent_favorites,
        'is_own_profile': is_own_profile,
    }
    return render(request, 'accounts/public_profile.html', context)


def public_list_view(request, username):
    """View a user's public video list (MyAnimeList style)"""
    profile_user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=profile_user)

    # Check if list is public
    is_own_list = request.user == profile_user
    if not profile.list_is_public and not is_own_list:
        raise Http404("This user's list is private.")

    # Get filter and sort params
    status_filter = request.GET.get('status', 'all')
    sort_by = request.GET.get('sort', '-updated_at')

    # Get list entries
    entries = VideoList.objects.filter(user=profile_user)
    if status_filter != 'all':
        entries = entries.filter(status=status_filter)

    # Sorting
    valid_sorts = ['-updated_at', '-score', 'score', 'title', '-title', '-added_at']
    if sort_by in valid_sorts:
        entries = entries.order_by(sort_by)

    # Get stats
    stats = VideoList.get_user_stats(profile_user)

    # Pagination
    paginator = Paginator(entries, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'entries': page_obj,
        'stats': stats,
        'current_status': status_filter,
        'current_sort': sort_by,
        'status_choices': VideoList.STATUS_CHOICES,
        'is_own_list': is_own_list,
        'total_count': paginator.count,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    }
    return render(request, 'accounts/public_list.html', context)
