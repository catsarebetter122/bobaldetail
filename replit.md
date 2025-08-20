# Overview

Cryptic Mobile Detailing Platform is a production-ready Flask web application for a mobile car detailing business. The platform features a customer-facing website with service booking capabilities and an admin dashboard for business management. Key features include real-time booking with availability checking, Stripe payment integration, automated email notifications, and a comprehensive admin panel for managing services and appointments.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Framework & Structure
- **Flask Application**: Uses Flask with SQLAlchemy ORM for database operations
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Application Factory Pattern**: Centralized app creation with extension initialization
- **Modular Design**: Separated concerns with dedicated files for routes, models, forms, and utilities

## Database Architecture
- **PostgreSQL Production Database**: Primary data store with SQLAlchemy ORM
- **Model Design**: 
  - User model with role-based access (admin/user)
  - Product model for services with status management (active/coming_soon)
  - Booking model with time slot validation and availability checking
  - Enum-based status fields for consistent state management
- **Data Relationships**: Foreign key relationships between users, bookings, and products
- **Business Rules**: 1 booking per customer per 7-day period enforced at database level

## Authentication & Authorization
- **Flask-Login**: Session-based authentication for admin users
- **Role-Based Access**: Admin and user roles with different permission levels
- **Password Security**: Werkzeug password hashing for secure credential storage
- **Protected Routes**: Login requirements for admin dashboard and management functions

## Frontend Architecture
- **Bootstrap 5**: Mobile-first responsive design with dark theme
- **Vanilla JavaScript**: Form validation, interactive elements, and user experience enhancements
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Custom CSS**: Brand-specific styling on top of Bootstrap framework

## Business Logic
- **Booking System**: Real-time availability checking with time slot validation
- **Service Management**: CRUD operations for detailing services with pricing
- **Payment Flow**: Stripe checkout integration with success/cancel handling
- **Email Automation**: Confirmation emails for bookings and business notifications

# External Dependencies

## Payment Processing
- **Stripe**: Complete payment processing with checkout sessions and webhook handling
- **Stripe API Integration**: Price management and payment status tracking

## Email Services
- **Flask-Mail**: SMTP email sending for notifications and confirmations
- **Email Templates**: HTML email templates for customer communications

## Database & Hosting
- **PostgreSQL**: Production database (configurable via DATABASE_URL)
- **SQLAlchemy**: ORM with connection pooling and migration support

## Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme support
- **Font Awesome**: Icon library for consistent visual elements
- **JavaScript Libraries**: Form validation and interactive components

## Development & Configuration
- **Environment Variables**: Configuration management for sensitive data and deployment settings
- **Werkzeug**: WSGI utilities and development server with proxy fix for deployment
- **Flask Extensions**: Login management, form handling, and mail integration