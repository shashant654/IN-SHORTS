from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(CustomUser)

admin.site.register(Category)
admin.site.register(NewsArticle)

admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)
admin.site.register(Payment)
admin.site.register(ArticleImage)


@admin.register(RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_role', 'status', 'created_at')
    list_filter = ('status', 'requested_role')
    search_fields = ('user__email',)