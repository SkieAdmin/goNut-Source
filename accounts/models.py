from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with preferences"""

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    PREFERENCE_CHOICES = [
        ('straight', 'Straight'),
        ('trans', 'Transexual'),
        ('gay', 'Gay'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    preference = models.CharField(max_length=10, choices=PREFERENCE_CHOICES, default='straight')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_api_gay_param(self):
        """
        Convert preference to Eporner API 'gay' parameter
        0 = straight content
        1 = gay content
        2 = both
        """
        if self.preference == 'straight':
            return 0
        elif self.preference == 'gay':
            return 1
        else:  # trans - show both
            return 2


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
