import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from jinja2 import Template
import logging
from fastapi import BackgroundTasks

async def send_email(
    recipient_email: str, 
    subject: str, 
    body: str,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str
):
    """Send an email using SMTP"""
    message = MIMEMultipart()
    message["From"] = smtp_username
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        logging.info(f"Email sent to {recipient_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {recipient_email}: {e}")
        raise

async def send_registration_email(
    email: str, 
    name: str, 
    frontend_url: str,
    background_tasks: BackgroundTasks,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str
):
    """Send a registration confirmation email"""
    template_path = Path(__file__).parent.parent / "templates/email/registration.html"
    with open(template_path) as file:
        template = Template(file.read())
    
    subject = "Welcome to Artisan Booking System"
    body = template.render(name=name, frontend_url=frontend_url)
    
    background_tasks.add_task(
        send_email,
        recipient_email=email,
        subject=subject,
        body=body,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password
    )

async def send_password_reset_email(
    email: str, 
    name: str, 
    reset_url: str,
    background_tasks: BackgroundTasks,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str
):
    """Send a password reset email"""
    template_path = Path(__file__).parent.parent / "templates/email/password_reset.html"
    with open(template_path) as file:
        template = Template(file.read())
    
    subject = "Password Reset Request"
    body = template.render(name=name, reset_url=reset_url)
    
    background_tasks.add_task(
        send_email,
        recipient_email=email,
        subject=subject,
        body=body,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password
    )

async def send_booking_confirmation_email(
    email: str, 
    name: str, 
    booking_details: dict,
    background_tasks: BackgroundTasks,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str
):
    """Send a booking confirmation email"""
    template_path = Path(__file__).parent.parent / "templates/email/booking_confirmation.html"
    with open(template_path) as file:
        template = Template(file.read())
    
    subject = "Your Booking Confirmation"
    body = template.render(name=name, booking_details=booking_details)
    
    background_tasks.add_task(
        send_email,
        recipient_email=email,
        subject=subject,
        body=body,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password
    )