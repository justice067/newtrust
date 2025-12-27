# views.py - CORRECTED VERSION (with duplicates removed)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from decimal import Decimal
import uuid
import os
from django.core.files.storage import default_storage, FileSystemStorage
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Account 

# Import all models
try:
    from .models import (
        Account, Transaction, LoanApplication, ContactMessage, 
        UserProfile, SystemSettings, MoneyTransfer, TransferStatusHistory,
        PaymentMethod, LoanPayment, LoanPaymentVerification
    )
    MODELS_LOADED = True
except ImportError as e:
    print(f"⚠️ Some models not loaded: {str(e)}")
    MODELS_LOADED = False
    # Import what we can
    try:
        from .models import Account, Transaction, LoanApplication, ContactMessage, UserProfile
    except:
        pass

# Company payment details (fallback if no payment methods are configured)
COMPANY_PAYMENT_DETAILS = {
    'bank_name': 'TrustBank',
    'account_name': 'TRUSTBANK LOAN SERVICES',
    'account_number': '1234567890',
    'usdt_address': 'TXYZ1234567890abcdef',
    'payment_instructions': 'Pay 10% of your loan amount to secure your application'
}

# ==================== HOME ====================
def home(request):
    """Home page - shows public info or redirects to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/index.html')

# ==================== DASHBOARD - FIXED ====================
@never_cache
@login_required(login_url='/login/')
def dashboard(request):
    """Dashboard page with account information - FIXED TO HANDLE MISSING MODELS"""
    print(f"📊 Dashboard accessed by: {request.user.username}")
    
    # Force correct user
    user_id = request.session.get('_auth_user_id')
    if user_id:
        try:
            correct_user = User.objects.get(id=user_id)
            request.user = correct_user
            print(f"🔄 FORCED USER: {correct_user.username} (ID: {correct_user.id})")
        except:
            pass
    
    request.session.modified = True
    
    try:
        # Get user account
        account = Account.objects.filter(user=request.user).first()
        
        # If user doesn't have an account yet, create one with 0.00
        if not account:
            account_number = str(uuid.uuid4())[:20]
            account = Account.objects.create(
                account_number=account_number,
                user=request.user,
                account_type='checking',
                balance=Decimal('0.00')
            )
            print(f"✅ Created new account for {request.user.username} with $0.00")
        
        # Get recent transactions
        try:
            transactions = Transaction.objects.filter(account=account).order_by('-created_at')[:10]
        except Exception as e:
            print(f"⚠️ Error fetching transactions: {str(e)}")
            transactions = []
        
        # Get active loans for this user
        try:
            loans = LoanApplication.objects.filter(user=request.user).order_by('-created_at')[:5]
        except Exception as e:
            print(f"⚠️ Error fetching loans: {str(e)}")
            loans = []
        
        # Get recent transfers for this user
        transfers = []
        try:
            if MODELS_LOADED:
                transfers = MoneyTransfer.objects.filter(sender=request.user).order_by('-created_at')[:5]
        except Exception as e:
            print(f"⚠️ Error fetching transfers: {str(e)}")
        
        # Get recent payments
        payments = []
        try:
            if MODELS_LOADED:
                payments = LoanPayment.objects.filter(loan__user=request.user).order_by('-created_at')[:5]
        except Exception as e:
            print(f"⚠️ Error fetching payments: {str(e)}")
        
        # Current time
        current_time = timezone.now()
        
        context = {
            'user': request.user,
            'account': account,
            'transactions': transactions,
            'loans': loans,
            'transfers': transfers,
            'payments': payments,
            'current_time': current_time,
        }
        
        print(f"💰 Balance for {request.user.username}: ${account.balance}")
        
        return render(request, 'core/dashboard.html', context)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in dashboard: {str(e)}")
        # Don't logout, just show error
        return render(request, 'core/dashboard.html', {
            'user': request.user,
            'error': 'There was an error loading dashboard data. Please try again.'
        })

# ==================== LOGIN ====================
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            return render(request, 'core/login.html', {'error': 'Please fill in all fields'})
        
        # Block "Admin" login attempt
        if email.lower() == "admin":
            return render(request, 'core/login.html', {
                'error': 'Cannot login as "Admin" - use your registered email'
            })
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            try:
                user_exists = User.objects.filter(username=email).exists()
                if user_exists:
                    return render(request, 'core/login.html', {'error': 'Incorrect password'})
                else:
                    return render(request, 'core/login.html', {'error': 'Account not found'})
            except:
                return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'core/login.html')

# ==================== REGISTER ====================
def register_view(request):
    """Handle user registration - FIXED TO BLOCK ADMIN"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        phone = request.POST.get('phone', '').strip()
        
        errors = []
        if not name:
            errors.append('Name is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        # Block dangerous emails
        dangerous_emails = ["admin", "administrator", "root", "superuser", "superadmin"]
        if email in dangerous_emails:
            errors.append('Cannot register with this email - choose a different one')
        
        if errors:
            return render(request, 'core/register.html', {'errors': errors})
        
        # Check if user already exists
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            return render(request, 'core/register.html', {'error': 'Email already registered'})
        
        try:
            # Create user with lowercase username
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name.split()[0] if ' ' in name else name,
                last_name=' '.join(name.split()[1:]) if ' ' in name else ''
            )
            
            # Ensure user is NOT staff
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            UserProfile.objects.create(
                user=user,
                phone=phone
            )
            
            account_number = str(uuid.uuid4())[:20]
            account = Account.objects.create(
                account_number=account_number,
                user=user,
                account_type='checking',
                balance=Decimal('0.00')
            )
            
            print(f"✅ Created account for {user.username} with $0.00")
            
            # Auto login after registration
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                return redirect('login')
                
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return render(request, 'core/register.html', {'error': f'Registration failed: {str(e)}'})
    
    return render(request, 'core/register.html')

# ==================== SAFE ADMIN ACCESS ====================
def safe_admin_access(request):
    """Safely access admin without losing user session"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Store current user info
    request.session['original_user'] = {
        'id': request.user.id,
        'username': request.user.username
    }
    
    # Log out to allow admin login
    logout(request)
    
    # Redirect to admin login
    return redirect('/admin/login/?next=/admin/')

# ==================== RESTORE USER SESSION ====================
def restore_user_session(request):
    """Restore original user session after admin work"""
    original_user = request.session.get('original_user')
    
    if original_user:
        try:
            user = User.objects.get(id=original_user['id'])
            login(request, user)
            print(f"✅ Restored session for {user.username}")
            return redirect('dashboard')
        except:
            pass
    
    return redirect('login')

# ==================== LOGOUT ====================
def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('home')

# ==================== CONTACT ====================
def contact(request):
    """Handle contact messages"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not all([name, email, subject, message]):
            return render(request, 'core/index.html', {'contact_error': 'Please fill all fields'})
        
        try:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            return redirect('home')
        except Exception as e:
            return render(request, 'core/index.html', {'contact_error': str(e)})
    
    return redirect('home')

# ==================== LOAN APPLICATION ====================

@login_required(login_url='/login/')
def loan_application_step1(request):
    """Step 1: Collect personal information - UPDATED TO SAVE DATA"""
    try:
        # Try to get payment methods if model exists
        payment_methods = []
        if MODELS_LOADED:
            try:
                payment_methods = PaymentMethod.objects.filter(is_active=True)
            except:
                pass
    except:
        payment_methods = []
    
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            location = request.POST.get('location', '').strip()
            full_address = request.POST.get('full_address', '').strip()
            date_of_birth = request.POST.get('date_of_birth', '').strip()
            security_question = request.POST.get('security_question', '').strip()
            security_answer = request.POST.get('security_answer', '').strip()
            
            # Validate all fields
            if not all([full_name, email, phone, location, full_address, date_of_birth, security_question, security_answer]):
                messages.error(request, 'Please fill all required fields')
                return render(request, 'core/loan_step1.html', {
                    'user': request.user,
                    'payment_methods': payment_methods
                })
            
            # Handle file uploads
            selfie_url = None
            if 'selfie' in request.FILES:
                selfie = request.FILES['selfie']
                file_path = default_storage.save(f'selfies/{request.user.id}_{selfie.name}', selfie)
                selfie_url = default_storage.url(file_path)
            
            id_document_url = None
            if 'id_document' in request.FILES:
                id_document = request.FILES['id_document']
                file_path = default_storage.save(f'id_documents/{request.user.id}_{id_document.name}', id_document)
                id_document_url = default_storage.url(file_path)
            
            address_proof_url = None
            if 'address_proof' in request.FILES:
                address_proof = request.FILES['address_proof']
                file_path = default_storage.save(f'address_proofs/{request.user.id}_{address_proof.name}', address_proof)
                address_proof_url = default_storage.url(file_path)
            
            # Save to session for step 2
            request.session['loan_data'] = {
                'step': 1,
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'location': location,
                'full_address': full_address,
                'date_of_birth': date_of_birth,
                'security_question': security_question,
                'security_answer': security_answer,
                'selfie_url': selfie_url,
                'id_document_url': id_document_url,
                'address_proof_url': address_proof_url,
            }
            
            messages.success(request, 'Personal information saved successfully!')
            return redirect('loan_step2')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'core/loan_step1.html', {
                'user': request.user,
                'payment_methods': payment_methods
            })
    
    return render(request, 'core/loan_step1.html', {
        'user': request.user,
        'payment_methods': payment_methods,
        'today': timezone.now().date()
    })



























# Step 2 - COMPATIBLE VERSION
@login_required(login_url='/login/')
def loan_application_step2(request):
    """Step 2: Loan details - SAVES TO DATABASE"""
    if 'loan_data' not in request.session:
        messages.error(request, 'Please complete step 1 first')
        return redirect('loan_step1')
    
    # Get payment methods from database
    payment_methods = []
    if MODELS_LOADED:
        try:
            payment_methods = PaymentMethod.objects.filter(is_active=True)
        except:
            pass
    
    if request.method == 'POST':
        try:
            loan_amount = request.POST.get('loan_amount', '0').strip()
            loan_purpose = request.POST.get('loan_purpose', '').strip()
            loan_term = request.POST.get('loan_term', '12').strip()
            
            # Get payment method
            payment_method_id = request.POST.get('payment_method', '').strip()
            sender_name = request.POST.get('sender_name', '').strip()
            sender_address = request.POST.get('sender_address', '').strip()
            sender_phone = request.POST.get('sender_phone', '').strip()
            transaction_id = request.POST.get('transaction_id', '').strip()
            payment_date = request.POST.get('payment_date', '').strip()
            
            # Calculate 10% deposit
            loan_amount_decimal = Decimal(loan_amount)
            deposit_amount = loan_amount_decimal * Decimal('0.10')
            
            if loan_amount_decimal < 100:
                messages.error(request, 'Minimum loan amount is $100')
                return redirect('loan_step2')
            
            # Get loan data from session
            loan_data = request.session['loan_data']
            
            # Get payment method
            payment_method = None
            if payment_method_id:
                try:
                    payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
                except:
                    pass
            
            # Generate application ID
            application_id = f"LOAN-{request.user.id}-{int(timezone.now().timestamp())}"
            
            # SAVE TO DATABASE
            loan = LoanApplication.objects.create(
                user=request.user,
                application_id=application_id,
                loan_type='personal',
                amount=loan_amount_decimal,
                purpose=loan_purpose,
                term_months=int(loan_term),
                
                # Personal Information
                full_name=loan_data['full_name'],
                email=loan_data['email'],
                phone=loan_data['phone'],
                location=loan_data['location'],
                full_address=loan_data['full_address'],
                date_of_birth=loan_data['date_of_birth'],
                security_question=loan_data['security_question'],
                security_answer=loan_data['security_answer'],
                selfie_url=loan_data.get('selfie_url'),
                id_document_url=loan_data.get('id_document_url'),
                address_proof_url=loan_data.get('address_proof_url'),
                
                # Payment Information
                payment_method=payment_method,
                payment_reference=transaction_id,
                
                # Status - CHANGED to 'pending' (you control from admin)
                status='pending',
                deposit_required=deposit_amount,
                deposit_paid=False,
            )
            
            # Create payment record if payment method exists
            if payment_method and MODELS_LOADED:
                try:
                    payment_proof = None
                    if 'payment_proof' in request.FILES:
                        payment_proof = request.FILES['payment_proof']
                    
                    payment = LoanPayment.objects.create(
                        loan=loan,
                        payment_method=payment_method,
                        amount_paid=deposit_amount,
                        transaction_id=transaction_id,
                        payment_date=payment_date,
                        sender_name=sender_name,
                        sender_address=sender_address,
                        sender_phone=sender_phone,
                        verified=False
                    )
                    
                    # Save payment proof file
                    if payment_proof:
                        fs = FileSystemStorage(location='media/loan_payments/')
                        filename = fs.save(f"{loan.application_id}_{payment_proof.name}", payment_proof)
                        payment.payment_proof = filename
                        payment.save()
                    
                    # Create verification record
                    LoanPaymentVerification.objects.create(
                        payment=payment,
                        status='pending',
                        notes='Payment submitted, awaiting verification'
                    )
                    
                except Exception as e:
                    print(f"⚠️ Could not create payment record: {str(e)}")
            
            messages.success(request, 'Loan application submitted successfully!')
            
            # Clear session data
            if 'loan_data' in request.session:
                del request.session['loan_data']
            
            # CHANGED: Redirect to confirmation page, NOT success page
            return redirect('loan_confirmation')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Pre-fill form with loan data
    loan_data = request.session.get('loan_data', {})
    
    return render(request, 'core/loan_step2.html', {
        'payment_methods': payment_methods,
        'loan_data': loan_data,
        'today': timezone.now().date()
    })











































# Step 3 - CONFIRMATION
@login_required(login_url='/login/')
def loan_confirmation(request):
    """Step 3: Show confirmation with current status"""
    # Get the most recent loan for this user
    try:
        loan = LoanApplication.objects.filter(
            user=request.user
        ).order_by('-created_at').first()
        
        if not loan:
            print("ERROR: No loan found for user!")
            return redirect('loan_step1')
            
        print(f"✅ Found loan in database. Status: {loan.status}")
        
        # Get payment details if available
        payment_details = None
        if MODELS_LOADED:
            try:
                payment_details = LoanPayment.objects.filter(loan=loan).first()
            except:
                pass
        
        # If loan is approved, redirect to success page
        if loan.status == 'approved':
            return redirect('loan_success')
        
    except Exception as e:
        print(f"ERROR checking loan: {str(e)}")
        return redirect('loan_step1')
    
    return render(request, 'core/loan_confirmation.html', {
        'loan': loan,
        'payment_details': payment_details
    })





























# ==================== SUCCESS PAGE ====================
@login_required(login_url='/login/')
def loan_success(request):
    """Show success page ONLY for APPROVED loans"""
    try:
        # Get the most recent APPROVED loan for this user
        loan = LoanApplication.objects.filter(
            user=request.user,
            status='approved'  # ONLY show approved loans
        ).order_by('-created_at').first()
        
        if loan:
            return render(request, 'core/loan_success.html', {
                'user': request.user,
                'loan': loan
            })
        else:
            # If no approved loan, redirect to confirmation
            messages.info(request, 'Your loan application is still pending approval.')
            return redirect('loan_confirmation')
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return redirect('loan_confirmation')


































# ==================== ADMIN VIEWS ====================

# Admin Loans
@login_required
def admin_loans(request):
    """Admin panel to view and manage loans"""
    if not request.user.is_staff:
        return redirect('dashboard')
    
    loans = LoanApplication.objects.all().order_by('-created_at')
    
    status_counts = {
        'pending_payment': loans.filter(status='pending_payment').count(),
        'under_review': loans.filter(status='under_review').count(),
        'approved': loans.filter(status='approved').count(),
        'rejected': loans.filter(status='rejected').count(),
        'disbursed': loans.filter(status='disbursed').count(),
        'completed': loans.filter(status='completed').count(),
        'total': loans.count()
    }
    
    return render(request, 'core/admin_loans.html', {
        'loans': loans,
        'status_counts': status_counts
    })

# Update Loan Status
@login_required
def update_loan_status(request, loan_id):
    """Update loan status (approve/reject)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        loan = LoanApplication.objects.get(id=loan_id)
        new_status = request.POST.get('status')
        
        if new_status in ['pending_payment', 'under_review', 'approved', 'rejected', 'disbursed', 'completed']:
            old_status = loan.status
            loan.status = new_status
            
            if new_status == 'approved' and old_status == 'under_review':
                account = Account.objects.filter(user=loan.user).first()
                if account:
                    loan_amount = loan.amount - loan.deposit_required
                    account.balance += loan_amount
                    account.save()
                    
                    Transaction.objects.create(
                        account=account,
                        transaction_type='loan_disbursement',
                        amount=loan_amount,
                        description=f'Loan Disbursement: {loan.purpose} (Application ID: {loan.application_id})'
                    )
                    
                    loan.deposit_paid = True
            
            loan.save()
            return JsonResponse({
                'success': True, 
                'new_status': loan.get_status_display(),
                'status_class': loan.status
            })
        
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    except LoanApplication.DoesNotExist:
        return JsonResponse({'error': 'Loan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# View Loan Details
@login_required
def view_loan_details(request, loan_id):
    """View details of a specific loan application"""
    try:
        loan = LoanApplication.objects.get(id=loan_id)
        
        if loan.user != request.user and not request.user.is_staff:
            return redirect('dashboard')
        
        # Get payments for this loan
        payments = []
        if MODELS_LOADED:
            try:
                payments = LoanPayment.objects.filter(loan=loan).order_by('-created_at')
            except:
                pass
        
        return render(request, 'core/loan_details.html', {
            'loan': loan,
            'payments': payments
        })
        
    except LoanApplication.DoesNotExist:
        return redirect('dashboard')

# ==================== PAYMENT METHODS ADMIN ====================

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_payment_methods(request):
    """Admin panel to manage payment methods"""
    if not MODELS_LOADED:
        messages.error(request, 'Payment methods module not available. Please run migrations.')
        return redirect('dashboard')
    
    payment_methods = PaymentMethod.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        if 'add_method' in request.POST:
            name = request.POST.get('name')
            payment_type = request.POST.get('payment_type')
            instructions = request.POST.get('instructions')
            account_name = request.POST.get('account_name')
            account_number = request.POST.get('account_number')
            wallet_address = request.POST.get('wallet_address')
            
            PaymentMethod.objects.create(
                name=name,
                payment_type=payment_type,
                instructions=instructions,
                account_name=account_name,
                account_number=account_number,
                wallet_address=wallet_address,
                is_active=True
            )
            messages.success(request, 'Payment method added successfully.')
            
        elif 'update_method' in request.POST:
            method_id = request.POST.get('method_id')
            try:
                method = PaymentMethod.objects.get(id=method_id)
                method.name = request.POST.get('name')
                method.payment_type = request.POST.get('payment_type')
                method.instructions = request.POST.get('instructions')
                method.account_name = request.POST.get('account_name')
                method.account_number = request.POST.get('account_number')
                method.wallet_address = request.POST.get('wallet_address')
                method.is_active = request.POST.get('is_active') == 'on'
                method.save()
                messages.success(request, 'Payment method updated successfully.')
            except PaymentMethod.DoesNotExist:
                messages.error(request, 'Payment method not found.')
        
        return redirect('admin_payment_methods')
    
    return render(request, 'core/admin_payment_methods.html', {
        'payment_methods': payment_methods,
        'payment_type_choices': PaymentMethod.PAYMENT_TYPES
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_loan_payments(request):
    """Admin panel to view and verify loan payments"""
    if not MODELS_LOADED:
        messages.error(request, 'Loan payments module not available. Please run migrations.')
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    payments = LoanPayment.objects.all()
    
    if status_filter != 'all':
        if status_filter == 'verified':
            payments = payments.filter(verified=True)
        elif status_filter == 'pending':
            payments = payments.filter(verified=False)
    
    if search_query:
        payments = payments.filter(
            Q(transaction_id__icontains=search_query) |
            Q(loan__application_id__icontains=search_query) |
            Q(sender_name__icontains=search_query) |
            Q(loan__user__username__icontains=search_query)
        )
    
    # Counts
    total_payments = LoanPayment.objects.count()
    verified_payments = LoanPayment.objects.filter(verified=True).count()
    pending_payments = LoanPayment.objects.filter(verified=False).count()
    
    context = {
        'payments': payments,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_payments': total_payments,
        'verified_payments': verified_payments,
        'pending_payments': pending_payments,
    }
    
    return render(request, 'core/admin_loan_payments.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def verify_loan_payment(request, payment_id):
    """Verify a loan payment"""
    if not MODELS_LOADED:
        messages.error(request, 'Loan payments module not available.')
        return redirect('dashboard')
    
    try:
        payment = LoanPayment.objects.get(id=payment_id)
        
        if request.method == 'POST':
            verify = request.POST.get('verify') == 'true'
            notes = request.POST.get('notes', '')
            
            payment.verified = verify
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.admin_notes = notes
            
            # Update loan status if payment is verified
            if verify:
                payment.loan.deposit_paid = True
                payment.loan.status = 'under_review'
                payment.loan.save()
            
            payment.save()
            
            # Update verification record
            LoanPaymentVerification.objects.create(
                payment=payment,
                status='verified' if verify else 'rejected',
                notes=notes,
                verified_by=request.user,
                verified_at=timezone.now()
            )
            
            messages.success(request, f'Payment {"verified" if verify else "rejected"} successfully.')
            return redirect('admin_loan_payments')
        
        # Get verification history
        verifications = LoanPaymentVerification.objects.filter(payment=payment).order_by('-created_at')
        
        return render(request, 'core/verify_loan_payment.html', {
            'payment': payment,
            'verifications': verifications
        })
        
    except LoanPayment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('admin_loan_payments')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_payment_detail(request, payment_id):
    """View payment details"""
    if not MODELS_LOADED:
        messages.error(request, 'Loan payments module not available.')
        return redirect('dashboard')
    
    try:
        payment = LoanPayment.objects.get(id=payment_id)
        verifications = LoanPaymentVerification.objects.filter(payment=payment).order_by('-created_at')
        
        return render(request, 'core/admin_payment_detail.html', {
            'payment': payment,
            'verifications': verifications
        })
        
    except LoanPayment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('admin_loan_payments')

# ==================== OTHER PAGES ====================

@login_required
def deposit(request):
    """Deposit funds page"""
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        account = None
    
    return render(request, 'core/deposit.html', {'account': account})

@login_required
def pay_bills(request):
    """Pay bills page"""
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        account = None
    
    current_time = timezone.now()
    
    return render(request, 'core/pay_bills.html', {
        'account': account,
        'current_time': current_time
    })

@login_required
def cards(request):
    """Cards management page"""
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        account = None
    
    current_time = timezone.now()
    
    return render(request, 'core/cards.html', {
        'user': request.user,
        'account': account,
        'current_time': current_time
    })

@login_required
def crypto(request):
    """Crypto trading page"""
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        account = None
    
    current_time = timezone.now()
    
    return render(request, 'core/crypto.html', {
        'account': account,
        'current_time': current_time
    })

@login_required
def transactions(request):
    """View all transactions"""
    try:
        account = Account.objects.get(user=request.user)
        user_transactions = Transaction.objects.filter(account=account).order_by('-created_at')
    except Account.DoesNotExist:
        account = None
        user_transactions = []
    
    return render(request, 'core/transactions.html', {
        'account': account,
        'transactions': user_transactions
    })

# ==================== SIMPLE ADMIN ====================

def admin_required(user):
    """Check if user is admin"""
    return user.is_authenticated and user.is_staff

@user_passes_test(admin_required, login_url='/login/')
def simple_admin(request):
    """Simple admin page to change balances - NO DJANGO ADMIN NEEDED"""
    message = ""
    message_type = ""
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_balance = request.POST.get('new_balance')
        
        try:
            # Get user account
            account = Account.objects.get(user_id=user_id)
            old_balance = account.balance
            account.balance = Decimal(new_balance)
            account.save()
            
            message = f"✅ Updated {account.user.email} from ${old_balance} to ${new_balance}"
            message_type = "success"
            
            print(f"ADMIN: Changed {account.user.email} balance to ${new_balance}")
            
        except Exception as e:
            message = f"❌ Error: {str(e)}"
            message_type = "error"
    
    # Get all users with their accounts
    users_data = []
    all_users = User.objects.all().order_by('id')
    
    for user in all_users:
        try:
            account = Account.objects.get(user=user)
            users_data.append({
                'id': user.id,
                'email': user.email,
                'balance': account.balance,
                'account_number': account.account_number
            })
        except:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'balance': 0.00,
                'account_number': 'N/A'
            })
    
    return render(request, 'core/simple_admin.html', {
        'users': users_data,
        'message': message,
        'message_type': message_type
    })

# ==================== SEND MONEY ====================
@login_required
def send_money(request):
    """Simple send money page - WORKS 100%"""
    # Get user's account
    account = Account.objects.filter(user=request.user).first()
    if not account:
        # Create account if doesn't exist
        account = Account.objects.create(
            account_number=str(uuid.uuid4())[:20],
            user=request.user,
            account_type='checking',
            balance=Decimal('0.00')
        )
    
    # ALWAYS show the send money page - no redirects!
    return render(request, 'core/send_money.html', {
        'user': request.user,
        'account': account
    })