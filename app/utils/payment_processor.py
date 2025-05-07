from typing import NamedTuple
import logging
from enum import Enum
from typing import Optional


class PaymentResult(NamedTuple):
    success: bool
    transaction_id: Optional[str]
    message: str

class PaymentProcessor:
    """Abstract base class for payment processors"""
    
    async def process_payment(
        self,
        method: str,
        amount: float,
        currency: str,
        token: str,
        description: str = ""
    ) -> PaymentResult:
        raise NotImplementedError

class StripeProcessor(PaymentProcessor):
    """Payment processor for Stripe"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def process_payment(
        self,
        method: str,
        amount: float,
        currency: str,
        token: str,
        description: str = ""
    ) -> PaymentResult:
        try:
            import stripe
            stripe.api_key = self.api_key
            
            # Convert amount to cents/pence
            amount_in_cents = int(amount * 100)
            
            
            charge = stripe.Charge.create(
                amount=amount_in_cents,
                currency=currency,
                source=token,
                description=description
            )
            
            if charge.paid:
                return PaymentResult(
                    success=True,
                    transaction_id=charge.id,
                    message="Payment successful"
                )
            else:
                return PaymentResult(
                    success=False,
                    transaction_id=charge.id,
                    message=charge.failure_message or "Payment failed"
                )
        except Exception as e:
            logging.error(f"Stripe payment error: {e}")
            return PaymentResult(
                success=False,
                transaction_id=None,
                message=str(e)
            )

class PayPalProcessor(PaymentProcessor):
    """Payment processor for PayPal"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def process_payment(
        self,
        method: str,
        amount: float,
        currency: str,
        token: str,
        description: str = ""
    ) -> PaymentResult:
        try:
            from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
            from paypalcheckoutsdk.orders import OrdersCaptureRequest
            
            
            environment = SandboxEnvironment(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            client = PayPalHttpClient(environment)
            
            request = OrdersCaptureRequest(token)
            response = client.execute(request)
            
            if response.result.status == "COMPLETED":
                return PaymentResult(
                    success=True,
                    transaction_id=response.result.id,
                    message="Payment successful"
                )
            else:
                return PaymentResult(
                    success=False,
                    transaction_id=response.result.id,
                    message="Payment failed"
                )
        except Exception as e:
            logging.error(f"PayPal payment error: {e}")
            return PaymentResult(
                success=False,
                transaction_id=None,
                message=str(e)
            )

async def process_payment(
    method: str,
    amount: float,
    token: str,
    settings
) -> PaymentResult:
    """Process a payment using the configured processor"""
    try:
        if settings.PAYMENT_PROCESSOR == "stripe":
            processor = StripeProcessor(settings.STRIPE_API_KEY)
        elif settings.PAYMENT_PROCESSOR == "paypal":
            processor = PayPalProcessor(
                settings.PAYPAL_CLIENT_ID,
                settings.PAYPAL_CLIENT_SECRET
            )
        else:
            raise ValueError("Invalid payment processor configured")
        
        return await processor.process_payment(
            method=method,
            amount=amount,
            currency="USD",  # Or get from settings
            token=token,
            description="Artisan Booking Service"
        )
    except Exception as e:
        logging.error(f"Payment processing error: {e}")
        return PaymentResult(
            success=False,
            transaction_id=None,
            message=str(e)
        )