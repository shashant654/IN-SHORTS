from django.db import models

# Create your models here.

from django.conf import settings
# Create your models here.

from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    alternate_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    trial_start_date = models.DateTimeField(auto_now_add=True)
    is_trial_active = models.BooleanField(default=True)
    subscription_active = models.BooleanField(default=False)
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('editor', 'Editor'),
        ('journalist', 'Journalist'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    
    def can_access_news(self):
        return self.subscription_active  
    
    def is_trial_expired(self):
        return (datetime.now().date() - self.trial_start_date.date()).days > 15
    
    def can_access_news(self):
        return not self.is_trial_expired() or self.subscription_active


    def can_upload_news(self):
        """Check if the user can upload news articles."""
        if self.is_superuser:
            return True
        
        # Check if user has required role
        if self.role not in ['editor', 'journalist']:
            return False  # This will trigger role change request
        
        # Check subscription for users with required role
        try:
            subscription = self.usersubscription
            if subscription.is_active and subscription.plan.can_upload_articles:
                upload_limit = subscription.plan.article_upload_limit
                current_uploads = NewsArticle.objects.filter(author=self).count()
                return current_uploads < upload_limit
        except UserSubscription.DoesNotExist:
            return False
        return False


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

class NewsArticle(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles',blank=True, null=True)
    heading_image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles', blank=True, null=True)
    title = models.CharField(max_length=200)
    summary = models.TextField(max_length=500)
    content = models.TextField()
    source_url = models.URLField()
    image_url = models.URLField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)

    def get_first_three_images(self):
        return self.images.all()[:3]

class ArticleImage(models.Model):
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='article_images/')

    def __str__(self):
        return f"Image for {self.article.title}"



class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField()
    features = models.TextField()
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True,blank=True, null=True) 
    image = models.ImageField(upload_to='subscription_images/', blank=True, null=True)
    can_upload_articles = models.BooleanField(default=False)
    article_upload_limit = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


from django.conf import settings

class RoleChangeRequest(models.Model):
    ROLE_CHOICES = [
        ('editor', 'Editor'),
        ('journalist', 'Journalist'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    requested_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} → {self.requested_role} ({self.status})"

    def get_requested_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.requested_role, self.requested_role)


from django.contrib.auth import get_user_model

User = get_user_model()


class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('netbanking', 'Netbanking'),
        ('card', 'Card'),
        ('bank', 'Bank'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
