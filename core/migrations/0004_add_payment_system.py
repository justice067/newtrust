# core/migrations/0004_add_payment_system.py - UPDATED
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # FIXED: Changed to match actual migration name
        ('core', '0003_moneytransfer_transferstatushistory'),
    ]

    operations = [
        # Create PaymentMethod model
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('payment_type', models.CharField(choices=[('walmart', 'Walmart Money Transfer'), ('bank_transfer', 'Bank Transfer'), ('western_union', 'Western Union'), ('moneygram', 'MoneyGram'), ('crypto', 'Cryptocurrency'), ('other', 'Other')], max_length=50)),
                ('instructions', models.TextField()),
                ('account_name', models.CharField(max_length=200)),
                ('account_number', models.CharField(blank=True, max_length=100)),
                ('wallet_address', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        
        # Add new fields to LoanApplication
        migrations.AddField(
            model_name='loanapplication',
            name='full_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='id_document_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='address_proof_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='payment_reference',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='payment_method',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.paymentmethod'),
        ),
        
        # Create LoanPayment model
        migrations.CreateModel(
            name='LoanPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=12)),
                ('transaction_id', models.CharField(max_length=100)),
                ('payment_date', models.DateField()),
                ('payment_proof', models.FileField(blank=True, null=True, upload_to='loan_payments/')),
                ('sender_name', models.CharField(blank=True, max_length=200)),
                ('sender_address', models.TextField(blank=True)),
                ('sender_phone', models.CharField(blank=True, max_length=20)),
                ('verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.loanapplication')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.paymentmethod')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_payments', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create LoanPaymentVerification model
        migrations.CreateModel(
            name='LoanPaymentVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='pending', max_length=50)),
                ('notes', models.TextField(blank=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to='core.loanpayment')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]