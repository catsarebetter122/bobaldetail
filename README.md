# Cryptic Mobile Detailing Platform

A production-ready Flask web application for Cryptic Mobile Detailing, featuring real-time booking, Stripe payments, and comprehensive business management.

## Features

### Customer Features
- **Mobile-Responsive Design**: Professional website optimized for all devices
- **Real-Time Booking System**: Live availability checking and appointment scheduling
- **Secure Payment Processing**: Stripe integration for safe online payments
- **Contact Management**: Direct contact forms and prominent phone display
- **Service Gallery**: Showcase of detailing work and services

### Business Management
- **Admin Dashboard**: Comprehensive business overview with revenue tracking
- **Product Management**: Full CRUD operations for services and pricing
- **Booking Management**: Track and manage all customer appointments
- **Email Notifications**: Automated confirmations and business alerts
- **1-Booking Per Week Rule**: Built-in customer booking restrictions

### Technical Features
- **Production Database**: PostgreSQL with SQLAlchemy ORM
- **Email Integration**: Flask-Mail for automated notifications
- **Form Validation**: Comprehensive client and server-side validation
- **Security**: Production-grade authentication and data protection
- **Mobile-First**: Responsive Bootstrap design

## Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, Vanilla JavaScript, Jinja2 templates
- **Payments**: Stripe API integration
- **Email**: Flask-Mail with SMTP
- **Authentication**: Flask-Login for admin access
- **Styling**: Custom CSS with Bootstrap theming

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Stripe account (for payments)
- Email service (Gmail, SendGrid, etc.)

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/cryptic_detailing

# Session Security
SESSION_SECRET=your-secret-key-here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=crypticmobiledetailing@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=crypticmobiledetailing@gmail.com

# Stripe Payment Processing
STRIPE_SECRET_KEY=sk_test_or_live_your_stripe_secret_key

# Admin Authentication
ADMIN_PASSWORD=secure-admin-password
