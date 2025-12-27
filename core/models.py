# models.py - UPDATED WITH PAYMENT METHOD MODELS
from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} Profile"

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('checking', 'Basic Checking'),
        ('savings', 'High-Yield Savings'),
        ('business', 'Business Banking'),
    ]

    account_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        import logging
        import uuid
        import time
        
        logger = logging.getLogger(__name__)
        
        # Log before save
        if self.id:
            old_balance = Account.objects.get(id=self.id).balance
            logger.info(f"🔧 MODEL: Updating account {self.id}, Old: ${old_balance}, New: ${self.balance}")
        else:
            logger.info(f"🔧 MODEL: Creating new account, balance: ${self.balance}")
        
        # Generate account number if not set
        if not self.account_number:
            self.account_number = f"ACC-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            logger.info(f"🔧 MODEL: Generated account number: {self.account_number}")
        
        super().save(*args, **kwargs)
        
        # Verify save
        self.refresh_from_db()
        logger.info(f"🔧 MODEL: Saved successfully! Account {self.id}, balance: ${self.balance}")

    def __str__(self):
        return f"{self.account_number} - {self.get_account_type_display()}"
        
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=255)
    recipient_account = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate transaction_id if not set
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type}"

# ==================== PAYMENT METHOD MODELS ====================

class PaymentMethod(models.Model):
    """Payment methods that admin can configure (Walmart, Bank, etc.)"""
    PAYMENT_TYPES = (
        ('walmart', 'Walmart Money Transfer'),
        ('bank_transfer', 'Bank Transfer'),
        ('western_union', 'Western Union'),
        ('moneygram', 'MoneyGram'),
        ('crypto', 'Cryptocurrency'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES)
    instructions = models.TextField()
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100, blank=True)
    wallet_address = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"
    
    class Meta:
        ordering = ['name']

# ==================== LOAN PAYMENT MODELS ====================

class LoanPayment(models.Model):
    """Track payments made for loans"""
    PAYMENT_STATUS = (
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('refunded', 'Refunded'),
    )
    
    loan = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    payment_date = models.DateField()
    sender_name = models.CharField(max_length=200)
    sender_address = models.TextField(blank=True)
    sender_phone = models.CharField(max_length=20, blank=True)
    payment_proof = models.FileField(upload_to='loan_payments/', blank=True, null=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id or self.id} - ${self.amount_paid}"

    class Meta:
        ordering = ['-created_at']

class LoanPaymentVerification(models.Model):
    """Track verification status of loan payments"""
    payment = models.ForeignKey(LoanPayment, on_delete=models.CASCADE, related_name='verifications')
    status = models.CharField(max_length=50, default='pending')
    notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Verification for Payment {self.payment.id} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']

# ==================== SINGLE LOAN APPLICATION MODEL ====================

class LoanApplication(models.Model):
    LOAN_STATUS = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('completed', 'Completed'),
    )
    
    LOAN_TYPES = (
        ('personal', 'Personal Loan'),
        ('business', 'Business Loan'),
        ('mortgage', 'Mortgage'),
        ('auto', 'Auto Loan'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    application_id = models.CharField(max_length=50, unique=True)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES, default='personal')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    term_months = models.IntegerField(default=12)
    
    # Personal Information - ALL FIELDS COMBINED
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    full_address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Security fields
    security_question = models.TextField(blank=True)
    security_answer = models.TextField(blank=True)
    
    # Document URLs
    selfie_url = models.URLField(blank=True, null=True)
    id_document_url = models.URLField(blank=True, null=True)
    address_proof_url = models.URLField(blank=True, null=True)
    
    # Payment fields
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    deposit_required = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='pending_payment')
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.application_id} - {self.user.username} - ${self.amount} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # If application_id is not set, generate one
        if not self.application_id:
            import time
            self.application_id = f"LOAN-{self.user.id if self.user else '0'}-{int(time.time())}"
        super().save(*args, **kwargs)

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

# ==================== MONEY TRANSFER MODELS ====================

class MoneyTransfer(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('crypto', 'Cryptocurrency'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    )
    
    # Sender Information
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='money_transfers')
    sender_name = models.CharField(max_length=200)
    sender_email = models.EmailField()
    sender_phone = models.CharField(max_length=20)
    
    # Recipient Information
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=20)
    recipient_country = models.CharField(max_length=100)
    recipient_bank_name = models.CharField(max_length=200, blank=True, null=True)
    recipient_account_number = models.CharField(max_length=100, blank=True, null=True)
    recipient_routing_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Transfer Details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    transfer_type = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    purpose = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Transaction Details
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    
    # Fees
    transfer_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Admin tracking
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_transfers')
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Generate unique reference number
            import time
            self.reference_number = f'TRF-{self.sender.id if self.sender else "0"}-{int(time.time())}'
        
        if not self.total_amount:
            self.total_amount = self.amount + self.transfer_fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.reference_number} - {self.sender_name} to {self.recipient_name} - ${self.amount}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Money Transfer'
        verbose_name_plural = 'Money Transfers'

class TransferStatusHistory(models.Model):
    """Track status changes for transfers"""
    transfer = models.ForeignKey(MoneyTransfer, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transfer.reference_number} - {self.status} at {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transfer Status History'
        verbose_name_plural = 'Transfer Status Histories'

# ==================== SYSTEM SETTINGS ====================

class SystemSettings(models.Model):
    """System-wide settings that admin can control"""
    name = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_setting(cls, name, default=None):
        try:
            setting = cls.objects.get(name=name)
            return setting.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, name, value, description=""):
        setting, created = cls.objects.get_or_create(
            name=name,
            defaults={'value': value, 'description': description}
        )
        if not created:
            setting.value = value
            setting.save()
        return setting