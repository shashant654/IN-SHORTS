from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('login/',login_page,name="login_page"),
    path('logout/',logout_page,name='logout_page'),
    path('register/',register,name="register"),
    path('my_profile/', my_profile, name='my_profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('news/', news_list, name='news_list'),
    path('article/<int:article_id>/', view_article, name='view_article'),

    path('subscriptions/', my_subscriptions, name='my_subscriptions'),
    
    path('plans/', subscription_plans, name='subscription_plans'),
    path('subscribe/method/<int:plan_id>/', choose_payment_method, name='choose_payment_method'),
    path('subscribe/razorpay/<int:plan_id>/', initiate_razorpay_payment, name='initiate_razorpay_payment'),
    path('subscribe/cash/<int:plan_id>/', pay_by_cash, name='pay_by_cash'),
    path('verify_payment/', verify_payment, name='verify_payment'),
    path('upload/', upload_article, name='upload_article'),
    path('request-role-change/', request_role_change, name='request_role_change'),
    path('my-articles/', my_articles, name='my_articles'),
    path('edit-article/<int:article_id>/', edit_article, name='edit_article'),
    path('articles/delete/<int:article_id>/', delete_article, name='delete_article'),

    path('enable-2fa/', enable_2fa, name='enable_2fa'),


]