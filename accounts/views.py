from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
