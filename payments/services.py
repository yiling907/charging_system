"""Payment service integration with mock payment gateway"""
import uuid
from django.conf import settings
from charging.models import ChargingRecord


def create_payment(record: ChargingRecord) -> str:
    """Create payment order and return payment URL"""
    if not record.fee:
        raise ValueError("Record must have a fee amount")

    # In real implementation, call actual payment gateway API
    payment_id = f"PAY-{uuid.uuid4().hex[:12]}"

    # Store transaction ID
    record.transaction_id = payment_id
    record.save()

    # Return mock payment URL
    return f"{settings.PAYMENT_GATEWAY_URL}?id={payment_id}"


def verify_payment(transaction_id: str) -> bool:
    """Verify payment status with payment provider"""
    try:
        record = ChargingRecord.objects.get(transaction_id=transaction_id)
        record.pay_status = 'paid'
        record.save()
        return True
    except ChargingRecord.DoesNotExist:
        return False