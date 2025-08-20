import os
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal

from app import app, db
from models import User, Product, Booking, Media, Contact, UserRole, ProductStatus, BookingStatus
from forms import ContactForm, BookingForm, AdminLoginForm, ProductForm
from utils import create_stripe_checkout_session, get_domain, send_booking_confirmation, send_booking_notification, send_contact_message

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'  # type: ignore
login_manager.login_message = 'Please log in to access the admin area.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Public Routes
@app.route('/')
def index():
    """Home page with hero section and service overview"""
    products = Product.query.filter_by(status=ProductStatus.ACTIVE).limit(3).all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    """Products/Services page"""
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    """Booking page with form"""
    form = BookingForm()
    
    if form.validate_on_submit():
        # Create booking record
        product = Product.query.get(form.product_id.data)
        if not product:
            flash('Invalid service selected.', 'error')
            return redirect(url_for('booking'))
        
        # Calculate end time (assume 2-hour service)
        end_time = form.start.data + timedelta(hours=2)
        
        booking = Booking(
            product_id=product.id,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            start=form.start.data,
            end=end_time,
            notes=form.notes.data
        )
        
        # If user is logged in, associate booking
        if current_user.is_authenticated:
            booking.user_id = current_user.id
        
        db.session.add(booking)
        db.session.commit()
        
        # Create Stripe checkout session
        domain = get_domain()
        success_url = f"https://{domain}/booking/success?booking_id={booking.id}"
        cancel_url = f"https://{domain}/booking/cancel?booking_id={booking.id}"
        
        checkout_session = create_stripe_checkout_session(product, success_url, cancel_url)
        
        if checkout_session:
            # Store booking ID in session for success/cancel handling
            session['pending_booking_id'] = booking.id
            return redirect(checkout_session.url)
        else:
            flash('Payment processing is currently unavailable. Please try again later.', 'error')
            db.session.delete(booking)
            db.session.commit()
    
    return render_template('booking.html', form=form)

@app.route('/booking/success')
def booking_success():
    """Booking payment success"""
    booking_id = request.args.get('booking_id')
    if not booking_id:
        booking_id = session.pop('pending_booking_id', None)
    
    if booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.status = BookingStatus.CONFIRMED
            booking.stripe_payment_id = request.args.get('payment_intent', 'completed')
            db.session.commit()
            
            # Send confirmation emails
            send_booking_confirmation(booking)
            send_booking_notification(booking)
            
            flash('Your booking has been confirmed! You will receive a confirmation email shortly.', 'success')
            return render_template('success.html', booking=booking)
    
    flash('Booking confirmation failed. Please contact us to verify your appointment.', 'error')
    return redirect(url_for('index'))

@app.route('/booking/cancel')
def booking_cancel():
    """Booking payment cancelled"""
    booking_id = request.args.get('booking_id')
    if not booking_id:
        booking_id = session.pop('pending_booking_id', None)
    
    if booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            # Delete the cancelled booking
            db.session.delete(booking)
            db.session.commit()
    
    flash('Booking was cancelled. No payment was processed.', 'info')
    return render_template('cancel.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form"""
    form = ContactForm()
    
    if form.validate_on_submit():
        # Store contact message in database
        contact = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=form.message.data
        )
        
        # Try to send email, but don't fail if it doesn't work
        contact_data = {
            'name': form.name.data,
            'email': form.email.data,
            'phone': form.phone.data,
            'message': form.message.data
        }
        
        email_sent = send_contact_message(contact_data)
        contact.email_sent = email_sent
        
        db.session.add(contact)
        db.session.commit()
        
        # Always show success message - we've stored the message even if email failed
        flash('Thank you for your message! We have received it and will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', form=form)

@app.route('/gallery')
def gallery():
    """Gallery page"""
    media_items = Media.query.order_by(Media.created_at.desc()).all()
    return render_template('gallery.html', media_items=media_items)

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
        return redirect(url_for('admin_dashboard'))
    
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data) and user.role == UserRole.ADMIN:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Get dashboard statistics
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status=BookingStatus.PENDING).count()
    confirmed_bookings = Booking.query.filter_by(status=BookingStatus.CONFIRMED).count()
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    
    # Revenue calculation (confirmed bookings only)
    confirmed_booking_list = Booking.query.filter_by(status=BookingStatus.CONFIRMED).all()
    total_revenue = sum(booking.product.price for booking in confirmed_booking_list)
    
    return render_template('admin/dashboard.html',
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         confirmed_bookings=confirmed_bookings,
                         recent_bookings=recent_bookings,
                         total_revenue=total_revenue)

@app.route('/admin/products')
@login_required
def admin_products():
    """Admin products management"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    """Add new product"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    form = ProductForm()
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            status=ProductStatus(form.status.data),
            is_membership=form.is_membership.data,
            stripe_price_id=form.stripe_price_id.data or None
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/products.html', form=form, edit_mode=False)

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    """Edit existing product"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.status = ProductStatus(form.status.data)
        product.is_membership = form.is_membership.data
        product.stripe_price_id = form.stripe_price_id.data or None
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/products.html', form=form, edit_mode=True, product=product)

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    """Delete product"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Check if product has associated bookings
    if product.bookings:
        flash('Cannot delete product with existing bookings.', 'error')
    else:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    
    return redirect(url_for('admin_products'))

def create_default_data():
    """Create default admin user and seed products"""
    # Create admin user if none exists
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    if not admin:
        admin_user = User(
            name='Admin',
            email='crypticmobiledetailing@gmail.com',
            role=UserRole.ADMIN
        )
        admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin_user)
    
    # Create default products if none exist
    if Product.query.count() == 0:
        # 1 active product at $75
        active_product = Product(
            name='Premium Mobile Detail',
            description='Complete interior and exterior detailing service. Includes wash, wax, interior cleaning, and tire shine.',
            price=Decimal('75.00'),
            status=ProductStatus.ACTIVE,
            is_membership=False
        )
        
        # 3 coming soon products
        coming_soon_products = [
            Product(
                name='Ceramic Coating Package',
                description='Professional ceramic coating application for long-lasting protection.',
                price=Decimal('299.00'),
                status=ProductStatus.COMING_SOON,
                is_membership=False
            ),
            Product(
                name='Paint Correction Service',
                description='Multi-stage paint correction to remove swirl marks and scratches.',
                price=Decimal('450.00'),
                status=ProductStatus.COMING_SOON,
                is_membership=False
            ),
            Product(
                name='Monthly Maintenance Plan',
                description='Monthly mobile detailing subscription for ongoing vehicle care.',
                price=Decimal('120.00'),
                status=ProductStatus.COMING_SOON,
                is_membership=True
            )
        ]
        
        db.session.add(active_product)
        for product in coming_soon_products:
            db.session.add(product)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating default data: {str(e)}")

# Initialize default data when the module is imported
with app.app_context():
    create_default_data()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
