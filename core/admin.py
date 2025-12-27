# core/admin.py - CORRECTED VERSION
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    Account, Transaction, LoanApplication, UserProfile, 
    ContactMessage, SystemSettings, MoneyTransfer, 
    TransferStatusHistory, PaymentMethod, LoanPayment, 
    LoanPaymentVerification
)
import logging

logger = logging.getLogger(__name__)

# ==================== CRITICAL FIX ====================
# Block auto-creation of "Admin" user
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def block_auto_admin(sender, instance, created, **kwargs):
    """STOP anyone from creating 'Admin' user"""
    if created and instance.username.lower() in ["admin", "administrator"]:
        print(f"🚨 SECURITY: Blocked auto-creation of '{instance.username}'")
        instance.delete()  # Delete it immediately
        raise ValueError("Cannot create user named 'Admin'")
# ==================== END FIX ====================

# ==================== LOAN APPLICATION ADMIN ====================





@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'user', 'full_name', 'amount', 'status', 'created_at', 'view_images')
    list_filter = ('status', 'created_at', 'loan_type')
    search_fields = ('application_id', 'user__username', 'full_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'applied_at', 'display_selfie', 'display_id_document', 'display_address_proof')
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application_id', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Loan Details', {
            'fields': ('loan_type', 'amount', 'purpose', 'term_months', 'deposit_required', 'deposit_paid')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone', 'location', 'full_address', 'date_of_birth')
        }),
        ('Security Information', {
            'fields': ('security_question', 'security_answer')
        }),
        ('Document Preview', {
            'fields': ('display_selfie', 'display_id_document', 'display_address_proof'),
            'classes': ('collapse',)
        }),
        ('Document URLs', {
            'fields': ('selfie_url', 'id_document_url', 'address_proof_url'),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'transaction_id')
        }),
    )
    
    def view_images(self, obj):
        if obj.selfie_url or obj.id_document_url or obj.address_proof_url:
            return format_html('<span style="color: green;">✅ Documents Available</span>')
        return format_html('<span style="color: red;">❌ No Documents</span>')
    view_images.short_description = 'Documents'
    
    def display_selfie(self, obj):
        if obj.selfie_url:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" /></a>', 
                             obj.selfie_url, obj.selfie_url)
        return "No selfie uploaded"
    display_selfie.short_description = 'Selfie Photo'
    
    def display_id_document(self, obj):
        if obj.id_document_url:
            if obj.id_document_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return format_html('<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" /></a>', 
                                 obj.id_document_url, obj.id_document_url)
            else:
                return format_html('<a href="{}" target="_blank" style="color: blue;">📄 View ID Document</a>', obj.id_document_url)
        return "No ID document uploaded"
    display_id_document.short_description = 'ID Document'
    
    def display_address_proof(self, obj):
        if obj.address_proof_url:
            if obj.address_proof_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return format_html('<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" /></a>', 
                                 obj.address_proof_url, obj.address_proof_url)
            else:
                return format_html('<a href="{}" target="_blank" style="color: blue;">📄 View Address Proof</a>', obj.address_proof_url)
        return "No address proof uploaded"
    display_address_proof.short_description = 'Address Proof'
    
    actions = ['approve_loans', 'reject_loans', 'mark_as_under_review', 'mark_as_disbursed']
    
    def approve_loans(self, request, queryset):
        """Approve selected loans"""
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} loans approved")
    approve_loans.short_description = "Approve selected loans"
    
    def reject_loans(self, request, queryset):
        """Reject selected loans"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} loans rejected")
    reject_loans.short_description = "Reject selected loans"
    
    def mark_as_under_review(self, request, queryset):
        """Mark selected loans as under review"""
        updated = queryset.update(status='under_review')
        self.message_user(request, f"{updated} loans marked as under review")
    mark_as_under_review.short_description = "Mark as under review"
    
    def mark_as_disbursed(self, request, queryset):
        """Mark selected loans as disbursed"""
        updated = queryset.update(status='disbursed')
        self.message_user(request, f"{updated} loans marked as disbursed")
    mark_as_disbursed.short_description = "Mark as disbursed"

# ==================== LOAN PAYMENT ADMIN ====================

@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('loan_link', 'payment_method', 'amount_paid', 'transaction_id', 
                    'verified', 'payment_date', 'created_at', 'view_payment_proof')
    list_filter = ('verified', 'created_at', 'payment_date')
    search_fields = ('loan__application_id', 'transaction_id', 'sender_name', 'sender_phone')
    readonly_fields = ('created_at', 'updated_at', 'display_payment_proof')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('loan', 'payment_method', 'amount_paid', 'transaction_id', 'payment_date')
        }),
        ('Sender Details', {
            'fields': ('sender_name', 'sender_address', 'sender_phone')
        }),
        ('Payment Proof', {
            'fields': ('payment_proof', 'display_payment_proof')
        }),
        ('Verification', {
            'fields': ('verified', 'verified_by', 'verified_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def loan_link(self, obj):
        if obj.loan:
            return format_html('<a href="/admin/core/loanapplication/{}/change/">{}</a>', 
                             obj.loan.id, obj.loan.application_id)
        return "No loan"
    loan_link.short_description = 'Loan Application'
    
    def view_payment_proof(self, obj):
        if obj.payment_proof:
            return format_html('<span style="color: green;">✅ Available</span>')
        return format_html('<span style="color: red;">❌ Missing</span>')
    view_payment_proof.short_description = 'Proof'
    
    def display_payment_proof(self, obj):
        if obj.payment_proof:
            file_url = obj.payment_proof.url
            if str(obj.payment_proof).lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return format_html('<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" /></a>', 
                                 file_url, file_url)
            else:
                return format_html('<a href="{}" target="_blank" style="color: blue;">📄 View Payment Proof</a>', file_url)
        return "No payment proof uploaded"
    display_payment_proof.short_description = 'Payment Proof Preview'
    
    actions = ['verify_payments', 'reject_payments']
    
    def verify_payments(self, request, queryset):
        """Verify selected payments"""
        from django.utils import timezone
        updated = queryset.update(verified=True, verified_by=request.user, verified_at=timezone.now())
        for payment in queryset:
            if payment.loan:
                payment.loan.deposit_paid = True
                if payment.loan.status == 'pending_payment':
                    payment.loan.status = 'under_review'
                payment.loan.save()
        self.message_user(request, f"{updated} payments verified")
    verify_payments.short_description = "Verify selected payments"
    
    def reject_payments(self, request, queryset):
        """Reject selected payments"""
        from django.utils import timezone
        updated = queryset.update(verified=False, verified_by=request.user, verified_at=timezone.now(), admin_notes='Payment rejected')
        self.message_user(request, f"{updated} payments rejected")
    reject_payments.short_description = "Reject selected payments"

# ==================== PAYMENT METHOD ADMIN ====================

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'payment_type', 'account_name', 'account_number', 'is_active', 'created_at')
    list_filter = ('payment_type', 'is_active', 'created_at')
    search_fields = ('name', 'account_name', 'account_number', 'wallet_address')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'payment_type', 'is_active')
        }),
        ('Bank/Account Details', {
            'fields': ('account_name', 'account_number', 'wallet_address'),
            'description': 'Add your bank name, account number, or wallet address here'
        }),
        ('Instructions for Users', {
            'fields': ('instructions',),
            'description': 'Write clear instructions for users on how to make payments'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Save payment method with proper formatting"""
        if obj.payment_type == 'bank_transfer' and not obj.account_number:
            from django.contrib import messages
            messages.warning(request, '⚠️ Please add bank account number for bank transfers')
        super().save_model(request, obj, form, change)
    
    actions = ['activate_methods', 'deactivate_methods']
    
    def activate_methods(self, request, queryset):
        """Activate selected payment methods"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} payment methods activated")
    activate_methods.short_description = "Activate selected methods"
    
    def deactivate_methods(self, request, queryset):
        """Deactivate selected payment methods"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} payment methods deactivated")
    deactivate_methods.short_description = "Deactivate selected methods"

# ==================== OTHER ADMIN CLASSES ====================

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'account_type', 'balance', 'created_at')
    list_filter = ('account_type', 'created_at')
    search_fields = ('account_number', 'user__username', 'user__email')
    readonly_fields = ('account_number', 'created_at', 'updated_at')
    
    # Allow admin to directly edit balance
    fields = ('user', 'account_number', 'account_type', 'balance', 'created_at', 'updated_at')
    
    # Add action to reset balances to 0
    actions = ['reset_to_zero']
    
    def reset_to_zero(self, request, queryset):
        """Reset selected accounts to $0.00"""
        updated = queryset.update(balance=0.00)
        self.message_user(request, f"{updated} accounts reset to $0.00")
    reset_to_zero.short_description = "Reset selected accounts to $0.00"
    
    def save_model(self, request, obj, form, change):
        """Save account WITHOUT messing with sessions"""
        super().save_model(request, obj, form, change)
        print(f"✅ Account {obj.account_number} updated. New balance: ${obj.balance}")

    def response_change(self, request, obj):
        """After saving, redirect properly"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        print(f"🔄 Admin updated account {obj.account_number}. Redirecting cleanly...")
        return HttpResponseRedirect(reverse('admin:core_account_changelist'))

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'account', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('transaction_id', 'account__account_number', 'description')
    readonly_fields = ('transaction_id', 'created_at')

@admin.register(MoneyTransfer)
class MoneyTransferAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'sender_name', 'recipient_name', 'amount', 'status', 'created_at')
    list_filter = ('status', 'transfer_type', 'created_at')
    search_fields = ('reference_number', 'sender_name', 'recipient_name', 'sender_email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'reference_number')
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('reference_number', 'status', 'transaction_id', 'admin_notes')
        }),
        ('Sender Information', {
            'fields': ('sender', 'sender_name', 'sender_email', 'sender_phone')
        }),
        ('Recipient Information', {
            'fields': ('recipient_name', 'recipient_email', 'recipient_phone', 
                      'recipient_country', 'recipient_bank_name', 
                      'recipient_account_number', 'recipient_routing_number')
        }),
        ('Transfer Details', {
            'fields': ('amount', 'transfer_fee', 'total_amount', 'currency', 
                      'transfer_type', 'payment_method', 'purpose')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at', 'processed_by')
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed']
    
    def mark_as_processing(self, request, queryset):
        """Mark selected transfers as processing"""
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} transfers marked as processing")
    mark_as_processing.short_description = "Mark selected as Processing"
    
    def mark_as_completed(self, request, queryset):
        """Mark selected transfers as completed"""
        from django.utils import timezone
        updated = queryset.update(status='completed', processed_at=timezone.now())
        self.message_user(request, f"{updated} transfers marked as completed")
    mark_as_completed.short_description = "Mark selected as Completed"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected transfers as failed"""
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} transfers marked as failed")
    mark_as_failed.short_description = "Mark selected as Failed"

@admin.register(TransferStatusHistory)
class TransferStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('transfer', 'status', 'changed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transfer__reference_number', 'notes')
    readonly_fields = ('created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    
    actions = ['mark_as_resolved', 'mark_as_unresolved']
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected messages as resolved"""
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f"{updated} messages marked as resolved")
    mark_as_resolved.short_description = "Mark selected as resolved"
    
    def mark_as_unresolved(self, request, queryset):
        """Mark selected messages as unresolved"""
        updated = queryset.update(is_resolved=False)
        self.message_user(request, f"{updated} messages marked as unresolved")
    mark_as_unresolved.short_description = "Mark selected as unresolved"

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'description')
    search_fields = ('name', 'value', 'description')

@admin.register(LoanPaymentVerification)
class LoanPaymentVerificationAdmin(admin.ModelAdmin):
    list_display = ('payment', 'status', 'verified_by', 'verified_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__loan__application_id', 'notes')
    readonly_fields = ('created_at',)

# ==================== SAFE USER ADMIN ====================

class SafeUserAdmin(admin.ModelAdmin):
    """Prevent creation of dangerous usernames"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name')
    
    def save_model(self, request, obj, form, change):
        """Block dangerous usernames"""
        dangerous_names = ["admin", "administrator", "root", "superuser"]
        
        if obj.username.lower() in dangerous_names and not obj.is_staff:
            from django.contrib import messages
            messages.error(request, f"Cannot create user '{obj.username}' - name reserved for staff only")
            return  # Don't save!
        
        super().save_model(request, obj, form, change)

# ==================== REGISTER MODELS ====================

# First, unregister default User admin
admin.site.unregister(User)

# Register with our safe version
admin.site.register(User, SafeUserAdmin)

# Note: All other models are registered using @admin.register decorator above

# ==================== ADMIN SITE CONFIG ====================
# Force admin to always ask for login (no auto-login)
admin.site.login_template = 'admin/login.html'
admin.site.logout_template = 'admin/logged_out.html'