from django.core.management.base import BaseCommand
from core.models import SystemSettings

class Command(BaseCommand):
    help = 'Setup default system settings for TrustBank'
    
    def handle(self, *args, **kwargs):
        """
        Creates default system settings if they don't exist.
        This should be run after migrations.
        """
        
        # Define default settings for your bank
        default_settings = [
            {
                'name': 'default_account_balance',
                'value': '0.00',
                'description': 'Default balance for new accounts'
            },
            {
                'name': 'min_deposit_amount',
                'value': '10.00',
                'description': 'Minimum deposit amount'
            },
            {
                'name': 'auto_logout_minutes',
                'value': '30',
                'description': 'Auto logout after minutes of inactivity'
            },
            {
                'name': 'loan_deposit_percentage',
                'value': '10',
                'description': 'Loan deposit percentage (10 = 10%)'
            },
            {
                'name': 'company_bank_account',
                'value': '1234567890',
                'description': 'Company bank account number for deposits'
            },
            {
                'name': 'company_usdt_address',
                'value': 'TXYZ1234567890abcdef',
                'description': 'Company USDT wallet address'
            },
            {
                'name': 'company_bank_name',
                'value': 'TrustBank',
                'description': 'Bank name for company account'
            },
            {
                'name': 'company_account_name',
                'value': 'TRUSTBANK LOAN SERVICES',
                'description': 'Account name for company account'
            },
            {
                'name': 'support_email',
                'value': 'support@trustbank.com',
                'description': 'Support email address'
            },
            {
                'name': 'support_phone',
                'value': '+1 (800) 123-4567',
                'description': 'Support phone number'
            },
            {
                'name': 'min_loan_amount',
                'value': '100',
                'description': 'Minimum loan amount ($)'
            },
            {
                'name': 'max_loan_amount',
                'value': '100000',
                'description': 'Maximum loan amount ($)'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Setting up default system settings..."))
        self.stdout.write("=" * 60)
        
        for setting_data in default_settings:
            name = setting_data['name']
            value = setting_data['value']
            description = setting_data['description']
            
            try:
                # Try to get existing setting
                setting, created = SystemSettings.objects.get_or_create(
                    name=name,
                    defaults={
                        'value': value,
                        'description': description
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Created: {name} = {value}")
                    )
                    created_count += 1
                else:
                    # Update if value has changed
                    if setting.value != value:
                        old_value = setting.value
                        setting.value = value
                        setting.description = description
                        setting.save()
                        self.stdout.write(
                            self.style.WARNING(f"↻ Updated: {name} from '{old_value}' to '{value}'")
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.NOTICE(f"● Already exists: {name} = {value}")
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error creating {name}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("SUMMARY:"))
        self.stdout.write(f"  Total settings processed: {len(default_settings)}")
        self.stdout.write(f"  New settings created: {created_count}")
        self.stdout.write(f"  Settings updated: {updated_count}")
        self.stdout.write(f"  Existing unchanged: {len(default_settings) - created_count - updated_count}")
        self.stdout.write("=" * 60)
        
        # Show all current settings
        self.stdout.write("\n" + self.style.SUCCESS("CURRENT SYSTEM SETTINGS:"))
        all_settings = SystemSettings.objects.all().order_by('name')
        
        if all_settings.exists():
            for s in all_settings:
                self.stdout.write(f"  {s.name:30} = {s.value:20} ({s.description})")
        else:
            self.stdout.write(self.style.WARNING("  No system settings found!"))
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✓ Default settings setup completed!"))