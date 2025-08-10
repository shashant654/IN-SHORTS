from django.core.management.base import BaseCommand
from accounts.models import Category, NewsArticle, SubscriptionPlan
from django.utils.text import slugify
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Seeds initial data for Category, NewsArticle, and SubscriptionPlan'

    def handle(self, *args, **kwargs):
        # ------------------ Seed Categories ------------------
        category_names = ['Politics', 'Technology', 'Sports', 'Health', 'Entertainment']
        categories = []

        for name in category_names:
            cat, created = Category.objects.get_or_create(
                name=name,
                slug=slugify(name)
            )
            categories.append(cat)

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(categories)} categories.'))

        # ------------------ Seed News Articles ------------------
        article_count = 30
        for i in range(article_count):
            NewsArticle.objects.create(
                title=f'Sample News Title {i+1}',
                summary='This is a short summary of the news article.',
                content='This is the full content of the news article.',
                source_url='https://example.com/sample-news',
                image_url='https://via.placeholder.com/300x200.png?text=News+Image',
                category=random.choice(categories),
                published_at=timezone.now(),
                is_featured=random.choice([True, False])
            )

        self.stdout.write(self.style.SUCCESS(f'Seeded {article_count} news articles.'))

        # ------------------ Seed Subscription Plans ------------------
        plans = [
            {
                'name': 'Basic Plan',
                'price': 49.99,
                'duration_months': 1,
                'features': 'Access to all news articles. No Ads.'
            },
            {
                'name': 'Premium Plan',
                'price': 129.99,
                'duration_months': 3,
                'features': 'Everything in Basic + Exclusive content.'
            },
            {
                'name': 'Annual Plan',
                'price': 399.99,
                'duration_months': 12,
                'features': 'All features with priority support.'
            },
        ]

        for plan in plans:
            SubscriptionPlan.objects.get_or_create(
                name=plan['name'],
                defaults={
                    'price': plan['price'],
                    'duration_months': plan['duration_months'],
                    'features': plan['features'],
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS('Seeded subscription plans successfully.'))
