from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()  # This gets your CustomUser model
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login,logout 
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import random
from django.conf import settings
from django.utils import timezone
import razorpay
from datetime import datetime
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.utils import timezone

from django.core.exceptions import PermissionDenied
import io
import qrcode
import pyotp


def home(request):
   
    articles = NewsArticle.objects.select_related('author', 'category').order_by('-published_at')
    return render(request, 'news/news_list.html', {'articles': articles})

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime

def register(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Validation
        if not first_name or not last_name or not email or not password:
            messages.error(request, 'All fields are required.')
            return redirect('/register/')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return redirect('/register/')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return redirect('/register/')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('/register/')

        # Create user
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email,
        )
        user.set_password(password)
        user.save()

        # ===== Send Welcome Email =====
        subject = "Welcome to NewsSite!"
        html_content = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_url': request.build_absolute_uri('/'),
            'year': datetime.now().year
        })
        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        messages.success(request, 'Account created successfully. A welcome email has been sent to your inbox.')
        return redirect('/login/')

    return render(request, 'register.html')

def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid email.')
            return redirect('/login/')

        user = authenticate(username=user.username, password=password)
        if user is not None:
            login(request, user)
            return redirect('news_list')  
        else:
            messages.error(request, 'Invalid password.')
            return render(request, 'login.html') 

    return render(request, 'login.html')

# ----------------------------------------- 
def logout_page(request):
      logout(request)
      return redirect('/login/')

@login_required
def enable_2fa(request):
    user = request.user
    uri = user.get_totp_uri()

    # Create QR code as base64
    import base64
    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    if request.method == "POST":
        code = request.POST.get("code")
        totp = pyotp.TOTP(user.get_or_create_otp_secret())
        if totp.verify(code):
            request.session['is_2fa_verified'] = True
            messages.success(request, "2FA enabled & verified successfully!")
            return redirect('my_profile')
        else:
            messages.error(request, "Invalid verification code.")

    return render(request, "enable_2fa.html", {"qr_code": qr_base64})

@login_required
def my_profile(request):
    user = request.user

    return render(request, 'my_profile.html', {
        'user': user,
    })

    
@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.mobile_number = request.POST.get('mobile_number')
        user.alternate_number = request.POST.get('alternate_number')
        user.gender = request.POST.get('gender')
        dob_str = request.POST.get('dob')
        if dob_str:
            user.dob = parse_date(dob_str)  # Converts "YYYY-MM-DD" to date
        else:
            user.dob = None  # Avoid invalid empty string
        user.city = request.POST.get('city')
        user.state = request.POST.get('state')
        user.country = request.POST.get('country')
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('my_profile')

    return render(request, 'edit_profile.html', {
        'user': user,
        'GENDER_CHOICES': User.GENDER_CHOICES
    })



@login_required
def news_list(request):
   
    articles = NewsArticle.objects.select_related('author', 'category').order_by('-published_at')
    return render(request, 'news/news_list.html', {'articles': articles})

@login_required
def view_article(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id)
    additional_images = article.images.all()  # Get all additional images
    
    if not request.user.subscription_active:
        # Free user - show limited content
        context = {
            'article': article,
            'is_subscribed': False,
            'additional_images': additional_images[:3]  # Show only first 3 images
        }
        return render(request, 'news/article_limited.html', context)
    
    # Paid user - show full content
    context = {
        'article': article,
        'is_subscribed': True,
        'additional_images': additional_images  # Show all images
    }
    return render(request, 'news/article_full.html', context)

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    user_subscription = None
    
    if request.user.subscription_active:
        try:
            user_subscription = UserSubscription.objects.get(user=request.user, is_active=True)
        except UserSubscription.DoesNotExist:
            pass
    
    context = {
        'plans': plans,
        'user_subscription': user_subscription,
        'current_date': timezone.now().date()
    }
    return render(request, 'subscriptions/plans.html', context)

@login_required
def my_subscriptions(request):
    user = request.user
    subscriptions = UserSubscription.objects.filter(user=user).order_by('-start_date')
    payments = Payment.objects.filter(user=user).order_by('-created_at')
    
    active_subscription = None
    if user.subscription_active:
        try:
            active_subscription = UserSubscription.objects.get(user=user, is_active=True)
        except UserSubscription.DoesNotExist:
            pass
    
    context = {
        'subscriptions': subscriptions,
        'payments': payments,
        'active_subscription': active_subscription,
        'current_date': timezone.now().date()
    }
    return render(request, 'subscriptions/my_subscriptions.html', context)

@login_required
def choose_payment_method(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    return render(request, 'subscriptions/choose_payment.html', {'plan': plan})


import razorpay

@login_required
def initiate_razorpay_payment(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    user = request.user

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment_amount = int(plan.price * 100)  # in paise

    razorpay_order = client.order.create({
        "amount": payment_amount,
        "currency": "INR",
        "receipt": f"receipt_{user.id}_{plan.id}",
        "payment_capture": 1
    })


    # Save payment
    Payment.objects.create(
        user=user,
        plan=plan,
        amount=plan.price,
        method='upi',  # could also be 'card', etc. based on selection
        razorpay_order_id=razorpay_order['id'],
    )

    context = {
        'plan': plan,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': payment_amount,
        'user': user,
    }

    return render(request, 'subscriptions/razorpay_payment.html', context)



@login_required
def verify_payment(request):
    order_id = request.GET.get('order_id')
    payment_id = request.GET.get('payment_id')

    try:
        payment = Payment.objects.get(razorpay_order_id=order_id)
        payment.razorpay_payment_id = payment_id
        payment.is_paid = True
        payment.save()

        # Activate subscription
        end_date = timezone.now() + timezone.timedelta(days=payment.plan.duration_months * 30)
        UserSubscription.objects.update_or_create(
            user=payment.user,
            defaults={'plan': payment.plan, 'end_date': end_date, 'is_active': True}
        )

        user = payment.user
        user.subscription_active = True
        user.is_trial_active = False
        user.save()

        messages.success(request, 'Payment successful! Subscription activated.')
        return redirect('news_list')
    except Payment.DoesNotExist:
        messages.error(request, 'Payment verification failed.')
        return redirect('subscription_plans')


@login_required
def pay_by_cash(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    user = request.user

    Payment.objects.create(
        user=user,
        plan=plan,
        amount=plan.price,
        method='cash',
        is_paid=True  # assuming cash will be collected offline
    )

    # Activate subscription immediately
    end_date = timezone.now() + timezone.timedelta(days=plan.duration_months * 30)
    UserSubscription.objects.update_or_create(
        user=user,
        defaults={'plan': plan, 'end_date': end_date, 'is_active': True}
    )
    user.subscription_active = True
    user.is_trial_active = False
    user.save()

    messages.success(request, 'Cash payment recorded. Subscription activated.')
    return redirect('news_list')


@login_required
def upload_article(request):
    user = request.user

    if not user.can_upload_news():
        # Check if user has a pending role change request
        pending_request = RoleChangeRequest.objects.filter(
            user=user, 
            status='pending'
        ).exists()
        
        if pending_request:
            messages.info(request, "Your role change request is pending admin approval. Please wait.")
            return redirect('news_list')
            
        if user.subscription_active and user.role == 'reader':
            messages.info(request, "Please request a role change to upload articles.")
            return redirect('request_role_change')
            
        messages.error(request, "You are not allowed to upload articles. Please check your subscription or article limit.")
        raise PermissionDenied

    # Rest of your existing view code...
    if request.method == 'POST':
        title = request.POST.get('title')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        source_url = request.POST.get('source_url')
        category_id = request.POST.get('category')
        heading_image = request.FILES.get('heading_image')
        published_at = timezone.now()

        category = Category.objects.get(id=category_id)

        article = NewsArticle.objects.create(
            title=title,
            summary=summary,
            content=content,
            source_url=source_url,
            category=category,
            heading_image=heading_image,
            author=user,
            published_at=published_at
        )

        for file in request.FILES.getlist('article_images'):
            ArticleImage.objects.create(article=article, image=file)

        messages.success(request, "Article uploaded successfully.")
        return redirect('news_list')

    categories = Category.objects.all()
    return render(request, 'news/upload_article.html', {'categories': categories})


from .models import RoleChangeRequest
from django.core.mail import send_mail
from django.template.loader import render_to_string
@login_required
def request_role_change(request):
    user = request.user

    # Check for any existing request (pending or otherwise)
    existing_request = RoleChangeRequest.objects.filter(user=user).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            messages.info(request, "Your role change request is already pending admin approval.")
            return redirect('news_list')
        elif existing_request.status == 'approved':
            messages.info(request, f"Your role has already been upgraded to {user.get_role_display()}.")
            return redirect('news_list')
        # If rejected, allow them to submit a new request

    if request.method == 'POST':
        selected_role = request.POST.get('role')

        if selected_role not in ['editor', 'journalist']:
            messages.error(request, "Invalid role selection.")
            return redirect('request_role_change')

        # Save in DB
        RoleChangeRequest.objects.create(
            user=user,
            requested_role=selected_role
        )

        # Send Email
        subject = f"Role Change Request from {user.get_full_name()}"
        message = render_to_string('emails/role_change_request.txt', {
            'user': user,
            'selected_role': selected_role,
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['shashantshekhar10@gmail.com'],
        )

        messages.success(request, "Your role change request has been sent to the admin.")
        return redirect('news_list')

    return render(request, 'request_role_change.html')

@login_required
def my_articles(request):
    articles = NewsArticle.objects.filter(author=request.user).order_by('-published_at')
    return render(request, 'news/my_articles.html', {'articles': articles})


@login_required
def edit_article(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id, author=request.user)
    
    if request.method == 'POST':
        article.title = request.POST.get('title')
        article.summary = request.POST.get('summary')
        article.content = request.POST.get('content')
        article.source_url = request.POST.get('source_url')
        article.category_id = request.POST.get('category')
        
        if 'heading_image' in request.FILES:
            article.heading_image = request.FILES['heading_image']
        
        article.save()
        
        # Handle additional images
        for file in request.FILES.getlist('article_images'):
            ArticleImage.objects.create(article=article, image=file)
        
        # Handle image deletion
        delete_ids = request.POST.getlist('delete_images')
        if delete_ids:
            ArticleImage.objects.filter(id__in=delete_ids, article=article).delete()
        
        messages.success(request, "Article updated successfully!")
        return redirect('my_articles')
    
    categories = Category.objects.all()
    return render(request, 'news/edit_article.html', {
        'article': article,
        'categories': categories
    })


@login_required
def delete_article(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id, author=request.user)
    
    if request.method == 'POST':
        article.deleted_at = timezone.now()
        article.save()
        messages.success(request, "Article has been deleted.")
        return redirect('my_articles')
    
    return redirect('my_articles')