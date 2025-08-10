from django.core.management.base import BaseCommand
from accounts.models import Category, NewsArticle, ArticleImage
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.timezone import now
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = "Seed demo categories, articles, and article images"

    def handle(self, *args, **kwargs):
        # Create sample categories
        categories_data = ['Politics', 'Technology', 'Sports', 'Health', 'Entertainment']
        categories = []

        for name in categories_data:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name)}
            )
            categories.append(category)

        self.stdout.write(self.style.SUCCESS("Categories created."))

        # Pick an existing user (for demo purpose, first superuser or any user)
        author = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not author:
            self.stdout.write(self.style.ERROR("No users found. Please create a user first."))
            return

        # Create sample articles
        articles = []
        for i, category in enumerate(categories):
            article, _ = NewsArticle.objects.get_or_create(
                title=f"Sample {category.name} Article",
                defaults={
                    'summary': f"This is a brief summary of {category.name.lower()} news.",
                    'content': f"This is the full content of the {category.name.lower()} article.",
                    'category': category,
                    'author': author,
                    'source_url': f"https://example.com/{category.slug}",
                    'image_url': f"https://example.com/media/sample-{category.slug}.jpg",
                    'published_at': now() - timedelta(days=i),
                    'is_featured': i % 2 == 0,
                }
            )
            articles.append(article)

        self.stdout.write(self.style.SUCCESS("News articles created."))

        # Add sample additional images for each article
        for article in articles:
            for i in range(1, 3):  # 2 images per article
                ArticleImage.objects.get_or_create(
                    article=article,
                    image=f"article_images/{slugify(article.title)}-{i}.jpg"
                )

        self.stdout.write(self.style.SUCCESS("Article images linked. Seeder complete."))
