from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, DecimalField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
from datetime import datetime, timedelta
from models import User, Booking, Product, ProductStatus, BookingStatus

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=500)])

class BookingForm(FlaskForm):
    product_id = SelectField('Service', coerce=int, validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    start = DateTimeField('Start Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    notes = TextAreaField('Additional Notes', validators=[Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        # Populate product choices with active products
        self.product_id.choices = [
            (p.id, f"{p.name} - ${p.price}") 
            for p in Product.query.filter_by(status=ProductStatus.ACTIVE).all()
        ]
    
    def validate_start(self, field):
        # Must be at least 24 hours in the future
        if field.data < datetime.now() + timedelta(hours=24):
            raise ValidationError('Booking must be at least 24 hours in advance.')
        
        # Must be during business hours (5 AM - 6 PM)
        if field.data.hour < 5 or field.data.hour >= 18:
            raise ValidationError('Bookings are only available between 5 AM and 6 PM.')
        
        # Check if time slot is available
        end_time = field.data + timedelta(hours=2)  # Assume 2-hour service duration
        if not Booking.check_availability(field.data, end_time):
            raise ValidationError('This time slot is not available.')
    
    def validate_email(self, field):
        # Check 7-day booking limit
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_booking = Booking.query.filter(
            Booking.email == field.data,
            Booking.start >= cutoff_date,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).first()
        if recent_booking:
            raise ValidationError('You can only book one service per 7-day period.')

class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[('active', 'Active'), ('coming_soon', 'Coming Soon')], validators=[DataRequired()])
    is_membership = BooleanField('Is Membership Product')
    stripe_price_id = StringField('Stripe Price ID', validators=[Length(max=100)])
