"""Email utility for sending appointment confirmations using Amazon SES."""

import os
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmailSender:
    """Handles sending appointment confirmation emails using Amazon SES."""
    
    def __init__(self):
        """Initialize email sender with Amazon SES settings."""
        # AWS credentials should be set via environment variables or AWS credentials file
        # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")  # SES is available in limited regions
        self.sender_email = "yao.dominican@gmail.com"  # Must be verified in SES
        self.sender_name = "Dr. Smith's Medical Office"
        
        # Initialize SES client
        try:
            self.ses_client = boto3.client(
                'ses',
                region_name=self.aws_region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize SES client: {e}")
            self.ses_client = None
    
    def send_appointment_confirmation(self, patient_data: Dict, appointment_time: str) -> bool:
        """
        Send appointment confirmation email using Amazon SES.
        
        Args:
            patient_data: Dictionary containing patient information
            appointment_time: Scheduled appointment time
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Get patient information
            name = patient_data.get('name', 'Patient')
            date_of_birth = patient_data.get('date_of_birth', 'Not provided')
            address = patient_data.get('address', 'Not provided')
            phone_number = patient_data.get('phone_number', 'Not provided')
            insurance = patient_data.get('payer_name', 'Not provided')
            chief_complaint = patient_data.get('chief_complaint', 'Not provided')
            
            # Create HTML email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Appointment Confirmation</h2>
                    <p>Dear <strong>{name}</strong>,</p>
                    
                    <p>Thank you for scheduling your appointment with Dr. Smith's office.</p>
                    
                    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2c5aa0;">
                        <h3 style="margin-top: 0; color: #2c5aa0;">Appointment Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Patient:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{name}</td></tr>
                            <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Date of Birth:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{date_of_birth}</td></tr>
                            <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Appointment Time:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee; color: #0066cc; font-weight: bold; font-size: 16px;">{appointment_time}</td></tr>
                            <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Address:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{address}</td></tr>
                            <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Phone:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{phone_number}</td></tr>
                            <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Insurance:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{insurance}</td></tr>
                            <tr><td style="padding: 8px 0;"><strong>Reason for Visit:</strong></td><td style="padding: 8px 0;">{chief_complaint}</td></tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h4 style="margin-top: 0; color: #856404;">Important Reminders:</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Please arrive 15 minutes early for check-in</li>
                            <li>Bring a valid photo ID and insurance card</li>
                            <li>Bring a list of current medications</li>
                            <li>If you need to cancel or reschedule, please call us at least 24 hours in advance</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions, please don't hesitate to contact our office.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="margin: 0;"><strong>Dr. Smith's Medical Office</strong></p>
                        <p style="margin: 5px 0;">Phone: (555) 123-4567</p>
                        <p style="margin: 5px 0;">Email: office@drsmith.com</p>
                    </div>
                    
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666; text-align: center;">This is an automated message. Please do not reply to this email.</p>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"""
Dear {name},

Thank you for scheduling your appointment with Dr. Smith's office.

APPOINTMENT CONFIRMATION
========================

Patient: {name}
Date of Birth: {date_of_birth}
Appointment Time: {appointment_time}
Address: {address}
Phone: {phone_number}
Insurance: {insurance}
Reason for Visit: {chief_complaint}

IMPORTANT REMINDERS:
- Please arrive 15 minutes early for check-in
- Bring a valid photo ID and insurance card
- Bring a list of current medications
- If you need to cancel or reschedule, please call us at least 24 hours in advance

If you have any questions, please don't hesitate to contact our office.

Best regards,
Dr. Smith's Medical Office
Phone: (555) 123-4567
Email: office@drsmith.com

This is an automated message. Please do not reply to this email.
            """
            
            # Log the email details
            logger.info("=== APPOINTMENT CONFIRMATION EMAIL ===")
            logger.info(f"To: jennyxiaoyao@gmail.com")
            logger.info(f"Subject: Appointment Confirmation - Dr. Smith's Office")
            logger.info(f"Patient: {name}")
            logger.info(f"Appointment: {appointment_time}")
            
            # Try to send email via Amazon SES
            if not self.ses_client:
                logger.error("❌ SES client not initialized - check AWS credentials")
                logger.info("📧 Email sending failed, but appointment is still scheduled")
                logger.info("=====================================")
                return False
            
            try:
                response = self.ses_client.send_email(
                    Destination={
                        'ToAddresses': ['jennyxiaoyao@gmail.com'],
                    },
                    Message={
                        'Body': {
                            'Html': {
                                'Charset': 'UTF-8',
                                'Data': html_content,
                            },
                            'Text': {
                                'Charset': 'UTF-8',
                                'Data': text_content,
                            },
                        },
                        'Subject': {
                            'Charset': 'UTF-8',
                            'Data': 'Appointment Confirmation - Dr. Smith\'s Office',
                        },
                    },
                    Source=f'{self.sender_name} <{self.sender_email}>',
                )
                
                logger.info(f"✅ Appointment confirmation email SENT successfully to jennyxiaoyao@gmail.com")
                logger.info(f"📧 SES Message ID: {response['MessageId']}")
                logger.info("=====================================")
                return True
                
            except ClientError as ses_error:
                error_code = ses_error.response['Error']['Code']
                error_message = ses_error.response['Error']['Message']
                
                if error_code == 'MessageRejected':
                    logger.error(f"❌ SES Error: Email rejected - {error_message}")
                    logger.info("📧 Check if sender email is verified in SES")
                elif error_code == 'InvalidParameterValue':
                    logger.error(f"❌ SES Error: Invalid parameter - {error_message}")
                elif error_code == 'ConfigurationSetDoesNotExist':
                    logger.error(f"❌ SES Error: Configuration issue - {error_message}")
                else:
                    logger.error(f"❌ SES Error ({error_code}): {error_message}")
                
                logger.info("📧 Email sending failed, but appointment is still scheduled")
                logger.info("=====================================")
                return False
                
            except Exception as ses_error:
                logger.error(f"❌ SES Error: {ses_error}")
                logger.info("📧 Please check AWS credentials and SES configuration")
                logger.info("📧 Email sending failed, but appointment is still scheduled")
                logger.info("=====================================")
                return False
            
        except Exception as e:
            logger.error(f"Failed to create appointment confirmation email: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email to verify email functionality."""
        test_data = {
            'name': 'Test Patient',
            'date_of_birth': '1990-01-01',
            'address': '123 Test St, Test City, CA 90210',
            'phone_number': '(555) 123-4567',
            'payer_name': 'Test Insurance',
            'chief_complaint': 'Test appointment'
        }
        
        return self.send_appointment_confirmation(test_data, "Tomorrow at 3:00 PM")
