import os
import stripe
from flask import current_app
from flask_mail import Message
from app import mail
from datetime import datetime

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def get_domain():
    """Get the current domain for Stripe redirects"""
    if os.environ.get('REPLIT_DEPLOYMENT'):
        return os.environ.get('REPLIT_DEV_DOMAIN')
    else:
        domains = os.environ.get('REPLIT_DOMAINS', '')
        if domains:
            return domains.split(',')[0]
    return 'localhost:5000'

def create_stripe_checkout_session(product, success_url, cancel_url):
    """
    Create a Stripe Checkout Session for a given ``product``.

    This helper abstracts away the details of constructing a Stripe Checkout
    Session.  It will either reference a preconfigured Stripe Price ID stored
    on the ``Product`` record (via the ``stripe_price_id`` field) or it will
    build a one‑off price on the fly using the product's name, description and
    price.  The price is converted to an integer number of cents to satisfy
    Stripe's API requirements.  If the product does not supply a Stripe Price
    ID, the currency defaults to USD.

    To enable automatic tax calculation – which allows Stripe to collect and
    remit sales tax based on the buyer's billing address – this function
    configures the Checkout Session to request an address from the customer.
    Stripe will calculate tax only if your account has Stripe Tax enabled and
    the provided billing address corresponds to a jurisdiction you have
    configured.  See https://stripe.com/docs/tax/checkout for details on
    enabling Stripe Tax in your account.

    The session collects the customer's billing address by setting
    ``billing_address_collection`` to ``"required"``, and it always creates
    a new customer in your Stripe account (``customer_creation='always'``).

    Args:
        product: A ``Product`` model instance describing the item being sold.
        success_url: The absolute URL to redirect the customer after a
            successful payment.
        cancel_url: The absolute URL to redirect the customer if they cancel
            the payment.

    Returns:
        A ``stripe.checkout.Session`` object on success, or ``None`` if
        creation failed (e.g. due to missing API key or Stripe error).
    """
    # Ensure a valid API key is present.  Without a key Stripe will reject all
    # requests with a cryptic error.  If the key is missing, log an error and
    # bail out early.
    if not stripe.api_key:
        current_app.logger.error(
            "Stripe API key is not configured. Set STRIPE_SECRET_KEY in your environment."
        )
        return None

    try:
        # Build the line items.  If a Stripe price has been stored on the
        # product, reference it directly.  Otherwise construct a one‑off
        # price using the product's attributes.  Convert the decimal price
        # to an integer number of cents using float() to avoid Decimal issues.
        if getattr(product, "stripe_price_id", None):
            line_items = [
                {
                    "price": product.stripe_price_id,
                    "quantity": 1,
                }
            ]
        else:
            line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": product.name,
                            "description": product.description,
                        },
                        "unit_amount": int(float(product.price) * 100),
                    },
                    "quantity": 1,
                }
            ]

        # Construct the Checkout Session parameters.  We enable automatic tax
        # calculation and require a billing address so Stripe can determine
        # the correct tax rate based on the buyer's location.  We also ask
        # Stripe to always create a Customer object for you so that the
        # address is stored on the customer record.  If you intend to ship
        # physical goods, you might instead use ``shipping_address_collection``.
        session_params = {
            "line_items": line_items,
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            # Automatically collect sales tax
            "automatic_tax": {"enabled": True},
            # Ask for the customer's billing address at checkout
            "billing_address_collection": "required",
            # Always create a Customer in your Stripe account
            "customer_creation": "always",
        }

        checkout_session = stripe.checkout.Session.create(**session_params)
        return checkout_session
    except Exception as e:
        # Log the exception for debugging.  Stripe errors will carry useful
        # information such as the error type and code.
        current_app.logger.error(f"Stripe checkout session creation failed: {e}")
        return None

def send_email(to, subject, template, **kwargs):
    """Send an email using Flask-Mail"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=template,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        return False

def send_booking_confirmation(booking):
    """Send booking confirmation email to client"""
    template = f"""
    <html>
    <body>
        <h2>Booking Confirmation - Cryptic Mobile Detailing</h2>
        
        <p>Dear {booking.name},</p>
        
        <p>Thank you for booking with Cryptic Mobile Detailing! Your appointment has been confirmed.</p>
        
        <h3>Booking Details:</h3>
        <ul>
            <li><strong>Service:</strong> {booking.product.name}</li>
            <li><strong>Date & Time:</strong> {booking.start.strftime('%B %d, %Y at %I:%M %p')}</li>
            <li><strong>Duration:</strong> Approximately 2 hours</li>
            <li><strong>Price:</strong> ${booking.product.price}</li>
        </ul>
        
        {f'<p><strong>Special Notes:</strong> {booking.notes}</p>' if booking.notes else ''}
        
        <p>If you need to reschedule or cancel, please contact us at least 24 hours in advance.</p>
        
        <p><strong>Contact Information:</strong><br>
        Phone: +1 (706) - 717 - 9406<br>
        Email: crypticmobiledetailing@gmail.com</p>
        
        <p>We look forward to providing you with exceptional mobile detailing service!</p>
        
        <p>Best regards,<br>
        Cryptic Mobile Detailing Team</p>
    </body>
    </html>
    """
    
    return send_email(
        booking.email,
        f"Booking Confirmation - {booking.product.name}",
        template
    )

def send_booking_notification(booking):
    """Send booking notification to business owner"""
    template = f"""
    <html>
    <body>
        <h2>New Booking Received</h2>
        
        <h3>Customer Information:</h3>
        <ul>
            <li><strong>Name:</strong> {booking.name}</li>
            <li><strong>Email:</strong> {booking.email}</li>
            <li><strong>Phone:</strong> {booking.phone}</li>
        </ul>
        
        <h3>Booking Details:</h3>
        <ul>
            <li><strong>Service:</strong> {booking.product.name}</li>
            <li><strong>Date & Time:</strong> {booking.start.strftime('%B %d, %Y at %I:%M %p')}</li>
            <li><strong>Price:</strong> ${booking.product.price}</li>
            <li><strong>Payment ID:</strong> {booking.stripe_payment_id or 'Pending'}</li>
        </ul>
        
        {f'<p><strong>Customer Notes:</strong> {booking.notes}</p>' if booking.notes else ''}
        
        <p>Login to the admin panel to manage this booking.</p>
    </body>
    </html>
    """
    
    return send_email(
        'crypticmobiledetailing@gmail.com',
        f"New Booking: {booking.product.name} - {booking.start.strftime('%m/%d/%Y')}",
        template
    )

def send_contact_message(form_data):
    """Send contact form message to business owner"""
    template = f"""
    <html>
    <body>
        <h2>New Contact Form Message</h2>
        
        <h3>Contact Information:</h3>
        <ul>
            <li><strong>Name:</strong> {form_data['name']}</li>
            <li><strong>Email:</strong> {form_data['email']}</li>
            <li><strong>Phone:</strong> {form_data['phone']}</li>
        </ul>
        
        <h3>Message:</h3>
        <p>{form_data['message']}</p>
        
        <p>Reply directly to this email to respond to the customer.</p>
    </body>
    </html>
    """
    
    return send_email(
        'crypticmobiledetailing@gmail.com',
        f"Contact Form: Message from {form_data['name']}",
        template
    )
