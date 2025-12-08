from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Custom registration form with gender and preference fields"""

    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='male'
    )

    preference = forms.ChoiceField(
        choices=UserProfile.PREFERENCE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='straight',
        label='Content Preference'
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'gender', 'preference']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Update or create the profile with preferences
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.gender = self.cleaned_data['gender']
            profile.preference = self.cleaned_data['preference']
            profile.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""

    class Meta:
        model = UserProfile
        fields = ['avatar', 'gender', 'preference']
        widgets = {
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'preference': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'avatar': 'Profile Picture',
            'preference': 'Content Preference',
        }


class UserUpdateForm(forms.ModelForm):
    """Form for updating user info (username, email)"""

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Styled password change form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
