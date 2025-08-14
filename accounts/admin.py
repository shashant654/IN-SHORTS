# admin.py
from django.core.mail import send_mail
from django.conf import settings
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

    def save_model(self, request, obj, form, change):
        # Detect status change to approved
        if change:  # editing an existing object
            old_obj = RoleChangeRequest.objects.get(pk=obj.pk)
            if old_obj.status != 'approved' and obj.status == 'approved':
                # Update the user's role
                obj.user.role = obj.requested_role
                obj.user.save()

                # Send approval email
                subject = "Your Role Change Request is Approved"
                message = f"""
Hi {obj.user.get_full_name()},

Good news! Your role change request to '{obj.get_requested_role_display()}' has been approved.
You can now upload articles on our platform.

Login and start contributing:
{request.scheme}://{request.get_host()}

Best regards,
The Admin Team
"""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [obj.user.email],
                )

        super().save_model(request, obj, form, change)
