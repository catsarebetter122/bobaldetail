from datetime import datetime, timedelta
from enum import Enum
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Numeric

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"

class ProductStatus(Enum):
    ACTIVE = "active"
    COMING_SOON = "coming_soon"

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MembershipStatus(Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    memberships = db.relationship('Membership', backref='user', lazy=True)
    media_uploads = db.relationship('Media', backref='uploader', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_book(self):
        """Check if user can make a new booking (1 per 7 days rule)"""
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_booking = Booking.query.filter(
            Booking.email == self.email,
            Booking.start >= cutoff_date,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).first()
        return recent_booking is None

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(ProductStatus), default=ProductStatus.ACTIVE, nullable=False)
    is_membership = db.Column(db.Boolean, default=False, nullable=False)
    stripe_price_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='product', lazy=True)
    memberships = db.relationship('Membership', backref='product', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Contact info (required even for logged-in users)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Booking details
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Payment info
    stripe_payment_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def check_availability(start_time, end_time, exclude_booking_id=None):
        """Check if the time slot is available"""
        query = Booking.query.filter(
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            db.or_(
                db.and_(Booking.start <= start_time, Booking.end > start_time),
                db.and_(Booking.start < end_time, Booking.end >= end_time),
                db.and_(Booking.start >= start_time, Booking.end <= end_time)
            )
        )
        
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
            
        return query.first() is None

class Membership(db.Model):
    __tablename__ = 'memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum(MembershipStatus), default=MembershipStatus.ACTIVE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Media(db.Model):
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    alt = db.Column(db.String(200), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    __tablename__ = 'contact'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contact {self.name} - {self.email}>'
