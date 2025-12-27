from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('contact/', views.contact, name='contact'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Loan application
    path('loan/step1/', views.loan_application_step1, name='loan_step1'),
    path('loan/step2/', views.loan_application_step2, name='loan_step2'),
    path('loan/confirmation/', views.loan_confirmation, name='loan_confirmation'),
    path('loan/success/', views.loan_success, name='loan_success'),
    path('loan/<int:loan_id>/', views.view_loan_details, name='view_loan_details'),
    
    # Banking features
    path('send-money/', views.send_money, name='send_money'),
    path('deposit/', views.deposit, name='deposit'),
    path('pay-bills/', views.pay_bills, name='pay_bills'),
    path('cards/', views.cards, name='cards'),
    path('crypto/', views.crypto, name='crypto'),
    path('transactions/', views.transactions, name='transactions'),
    
    # Admin pages
    path('admin/loans/', views.admin_loans, name='admin_loans'),
    path('admin/loans/<int:loan_id>/update/', views.update_loan_status, name='update_loan_status'),
    path('admin/payment-methods/', views.admin_payment_methods, name='admin_payment_methods'),
    path('admin/loan-payments/', views.admin_loan_payments, name='admin_loan_payments'),
    path('admin/loan-payments/<int:payment_id>/', views.admin_payment_detail, name='admin_payment_detail'),
    path('admin/loan-payments/<int:payment_id>/verify/', views.verify_loan_payment, name='verify_loan_payment'),
    path('simple-admin/', views.simple_admin, name='simple_admin'),
    
    # Session management
    path('safe-admin/', views.safe_admin_access, name='safe_admin_access'),
    path('restore-session/', views.restore_user_session, name='restore_user_session'),
]