from django.db import migrations

def add_subscription_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('properties', 'SubscriptionPlan')
    SubscriptionPlan.objects.create(
        name="Basic Plan", plan_type="BASIC", price=2000.00, duration_days=30,
        description="Unlimited views", is_active=True
    )
    SubscriptionPlan.objects.create(
        name="Premium Plan", plan_type="PREMIUM", price=5000.00, duration_days=30,
        description="Exclusive listings", exclusive_access=True, is_active=True
    )
    SubscriptionPlan.objects.create(
        name="Agent Plan", plan_type="AGENT", price=10000.00, duration_days=30,
        description="Listing management", exclusive_access=True, listing_management=True, is_active=True
    )

class Migration(migrations.Migration):
    dependencies = [('properties', '0001_initial')]
    operations = [migrations.RunPython(add_subscription_plans)]  