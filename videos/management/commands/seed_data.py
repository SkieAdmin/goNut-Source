from django.core.management.base import BaseCommand
from videos.models import Category, Tag


class Command(BaseCommand):
    help = 'Seed initial categories and tags'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Amateur', 'description': 'Amateur content'},
            {'name': 'Asian', 'description': 'Asian content'},
            {'name': 'Latina', 'description': 'Latina content'},
            {'name': 'Ebony', 'description': 'Ebony content'},
            {'name': 'MILF', 'description': 'MILF content'},
            {'name': 'Teen', 'description': '18+ Teen content'},
            {'name': 'Blonde', 'description': 'Blonde content'},
            {'name': 'Brunette', 'description': 'Brunette content'},
            {'name': 'Redhead', 'description': 'Redhead content'},
            {'name': 'BBW', 'description': 'BBW content'},
            {'name': 'Lesbian', 'description': 'Lesbian content'},
            {'name': 'Solo', 'description': 'Solo content'},
            {'name': 'Threesome', 'description': 'Threesome content'},
            {'name': 'Anal', 'description': 'Anal content'},
            {'name': 'Blowjob', 'description': 'Blowjob content'},
            {'name': 'Pinay', 'description': 'Filipino content'},
        ]

        tags = [
            'HD', '4K', 'POV', 'Hardcore', 'Softcore', 'Creampie',
            'Big Tits', 'Small Tits', 'Big Ass', 'Petite', 'Curvy',
            'Facial', 'Cumshot', 'Deepthroat', 'Doggystyle', 'Missionary',
            'Cowgirl', 'Reverse Cowgirl', 'Massage', 'Oiled', 'Wet',
            'Outdoor', 'Public', 'Homemade', 'Professional', 'Verified',
        ]

        self.stdout.write('Creating categories...')
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f'  Created: {category.name}')

        self.stdout.write('Creating tags...')
        for tag_name in tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                self.stdout.write(f'  Created: {tag.name}')

        self.stdout.write(self.style.SUCCESS('Seed data created successfully!'))
