from django import forms
from django.core.validators import FileExtensionValidator
from .models import Video, Category, Tag


class VideoUploadForm(forms.ModelForm):
    """Form for uploading new videos"""

    ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'webm', 'mov', 'avi', 'mkv']
    ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB

    video_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mov', 'avi', 'mkv'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'video/mp4,video/webm,video/quicktime,video/x-msvideo,video/x-matroska'
        }),
        help_text='Supported formats: MP4, WebM, MOV, AVI, MKV. Max size: 500MB'
    )

    thumbnail = forms.ImageField(
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif,image/webp'
        }),
        help_text='Recommended: 16:9 aspect ratio, at least 1280x720px'
    )

    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas (e.g., tag1, tag2, tag3)'
        }),
        help_text='Separate tags with commas'
    )

    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file', 'thumbnail', 'category', 'quality']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title',
                'maxlength': '255'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter video description (optional)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quality': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = 'Select a category'
        self.fields['category'].required = False  # Make category optional
        self.fields['description'].required = False

        # If editing, populate tags_input
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )

    def clean_video_file(self):
        video = self.cleaned_data.get('video_file')
        if video:
            if video.size > self.MAX_VIDEO_SIZE:
                raise forms.ValidationError(
                    f'Video file too large. Maximum size is {self.MAX_VIDEO_SIZE // (1024*1024)}MB.'
                )
        return video

    def clean_thumbnail(self):
        image = self.cleaned_data.get('thumbnail')
        if image:
            if image.size > self.MAX_IMAGE_SIZE:
                raise forms.ValidationError(
                    f'Image file too large. Maximum size is {self.MAX_IMAGE_SIZE // (1024*1024)}MB.'
                )
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # Handle tags
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
                instance.tags.clear()
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    instance.tags.add(tag)
            else:
                instance.tags.clear()

        return instance


class VideoEditForm(forms.ModelForm):
    """Form for editing existing videos (no video file change)"""

    ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

    thumbnail = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif,image/webp'
        }),
        help_text='Leave empty to keep current thumbnail'
    )

    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas'
        }),
        help_text='Separate tags with commas'
    )

    class Meta:
        model = Video
        fields = ['title', 'description', 'thumbnail', 'category', 'quality', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title',
                'maxlength': '255'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter video description'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quality': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = 'Select a category'
        self.fields['description'].required = False

        # Populate tags_input from existing tags
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )

    def clean_thumbnail(self):
        image = self.cleaned_data.get('thumbnail')
        if image and hasattr(image, 'size'):
            if image.size > self.MAX_IMAGE_SIZE:
                raise forms.ValidationError(
                    f'Image file too large. Maximum size is {self.MAX_IMAGE_SIZE // (1024*1024)}MB.'
                )
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # Handle tags
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
                instance.tags.clear()
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    instance.tags.add(tag)
            else:
                instance.tags.clear()

        return instance
