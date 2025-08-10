from django.core.management.base import BaseCommand
from accounts.models import SubscriptionPlan
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed database with default subscription plans'

    def handle(self, *args, **kwargs):
        plans = [
            {
                'name': 'Basic Plan',
                'price': 49.99,
                'duration_months': 1,
                'features': 'Access to all news articles. No Ads.',
                'image': 'subscription_images/planBasic.jpg',
                'can_upload_articles': False
            },
            {
                'name': 'Premium Plan',
                'price': 129.99,
                'duration_months': 3,
                'features': 'Everything in Basic + Exclusive content.',
                'image': 'subscription_images/planPremium.jpg',
                'can_upload_articles': False
            },
            {
                'name': 'Annual Plan',
                'price': 399.99,
                'duration_months': 12,
                'features': 'All features with priority support.',
                'image': 'subscription_images/planAnnual.jpg',
                'can_upload_articles': True  # ✅ Enable article upload
            }
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'price': plan_data['price'],
                    'duration_months': plan_data['duration_months'],
                    'features': plan_data['features'],
                    'slug': slugify(plan_data['name']),
                    'image': plan_data['image'],
                    'can_upload_articles': plan_data['can_upload_articles'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {plan.name}"))
            else:
                # Optional: update the can_upload_articles field if needed
                plan.can_upload_articles = plan_data['can_upload_articles']
                plan.save()
                self.stdout.write(self.style.WARNING(f"Updated: {plan.name}"))
