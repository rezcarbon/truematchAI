# Email Configuration Guide

TrueMatch supports three email delivery methods. Choose ONE provider for your environment.

## Quick Setup

### Option 1: Gmail (Recommended for Development)

1. **Enable App Passwords:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Generate an app-specific password

2. **Set Environment Variables:**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-specific-password  # NOT your Gmail password!
   SMTP_FROM_EMAIL=noreply@truematch.ai
   SMTP_FROM_NAME=TrueMatch
   SMTP_USE_TLS=true
   ```

3. **Test:**
   ```bash
   python -c "from app.services.email_service import EmailService; import asyncio; asyncio.run(EmailService.send_notification_email('test@example.com', 'Test', 'Hello'))"
   ```

---

### Option 2: SendGrid (Recommended for Production)

1. **Create SendGrid Account:**
   - Sign up at https://sendgrid.com
   - Create an API key in Settings > API Keys

2. **Install Library:**
   ```bash
   pip install sendgrid
   ```

3. **Set Environment Variables:**
   ```bash
   SENDGRID_API_KEY=SG.your-api-key-here
   ```

4. **Implementation Status:**
   - Currently stubbed (see `/app/services/email_service.py` line 246-250)
   - Implementation template ready for SendGrid library
   - TODO: Implement the `_send_via_sendgrid()` method

---

### Option 3: AWS SES (Recommended for AWS Deployments)

1. **Enable SES in AWS Console:**
   - Go to SES in your AWS region
   - Verify your sender email address
   - Request production access (if not in sandbox)

2. **Install Library:**
   ```bash
   pip install boto3
   ```

3. **Set Environment Variables:**
   ```bash
   AWS_SES_REGION=us-east-1  # or your region
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   ```

4. **Implementation Status:**
   - Currently stubbed (see `/app/services/email_service.py` line 251-255)
   - Implementation template ready for boto3
   - TODO: Implement the `_send_via_aws_ses()` method

---

## Environment Variables

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `SMTP_SERVER` | Yes (SMTP) | `smtp.gmail.com` | Hostname of SMTP server |
| `SMTP_PORT` | Yes (SMTP) | `587` | TLS: 587, SMTPS: 465, Plain: 25 |
| `SMTP_USERNAME` | Yes (SMTP) | `sender@gmail.com` | Account email for authentication |
| `SMTP_PASSWORD` | Yes (SMTP) | `app-password` | Use app-specific password for Gmail |
| `SMTP_FROM_EMAIL` | No | `noreply@truematch.ai` | Default: noreply@truematch.ai |
| `SMTP_FROM_NAME` | No | `TrueMatch` | Default: TrueMatch |
| `SMTP_USE_TLS` | No | `true` | Use STARTTLS (port 587). False = SMTPS (port 465) |
| `SENDGRID_API_KEY` | Yes (SendGrid) | `SG.xxx...` | SendGrid API key |
| `AWS_SES_REGION` | Yes (AWS SES) | `us-east-1` | AWS region where SES is enabled |
| `AWS_ACCESS_KEY_ID` | Yes (AWS SES) | `AKIA...` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Yes (AWS SES) | `xxx...` | AWS secret key |

---

## How Email Notifications Work

### Email Delivery Flow

1. **Event Triggered** (Interview scheduled, candidate advanced, scorecard submitted)
   ```python
   await NotificationService.create_notification(
       db=db,
       user_id=user_id,
       notification_type="interview_scheduled",
       title="Interview scheduled",
       message="...",
   )
   ```

2. **Notification Created** in database with status:
   - `read = False`
   - `delivered = False` (in-app)
   - `email_sent = False`

3. **WebSocket Broadcast** to connected users (real-time delivery)

4. **Email Queued** via Celery task:
   ```python
   send_notification_email.delay(
       user_id=user_id,
       notification_id=notification_id,
       recipient_email=user.email,
       title=title,
       message=message,
   )
   ```

5. **Email Sent** via configured provider (SMTP/SendGrid/SES)
   - Database updated: `email_sent = True`, `email_sent_at = now`

6. **User Receives Email** with:
   - Subject: Custom per notification type
   - Body: Formatted with context variables
   - Action link: Direct link to relevant resource

---

## Email Templates

Email templates are defined in `/app/services/email_service.py`:

### Available Templates

- **interview_scheduled**: Interview confirmation with meeting link
- **scorecard_request**: Request to complete interview scorecard
- **candidate_advanced**: Notification when candidate moves to next stage
- **pipeline_update**: General pipeline change notification
- **system_alert**: System-level alerts

### Customizing Templates

Edit the `TEMPLATES` dict in `EmailService`:

```python
TEMPLATES = {
    "interview_scheduled": {
        "subject": "Interview Scheduled for {candidate_name}",
        "body": """
Dear {recruiter_name},
...
        """,
    },
    # Add more templates here
}
```

Variables available:
- `{candidate_name}`, `{recruiter_name}`, `{position_title}`
- `{scheduled_at}`, `{location}`, `{action_url}`
- Any context variable you pass in notification creation

---

## Quiet Hours

Users can set quiet hours to prevent email notifications during specific times (e.g., 22:00-08:00):

```python
NotificationPreference(
    quiet_hours_enabled=True,
    quiet_hours_start="22:00",  # 10 PM
    quiet_hours_end="08:00",    # 8 AM
)
```

The email service checks quiet hours before sending:
- If current time is within quiet hours, email is NOT sent
- In-app notification still delivered (not affected by quiet hours)
- Email will be retried outside quiet hours window

---

## Troubleshooting

### Emails Not Sending

1. **Check Configuration:**
   ```bash
   # Verify SMTP settings are set
   echo $SMTP_SERVER
   echo $SMTP_PORT
   echo $SMTP_USERNAME
   ```

2. **Check Logs:**
   ```bash
   # View error logs
   docker logs truematch-api | grep "email\|SMTP\|Email"
   ```

3. **Test SMTP Connection:**
   ```python
   import smtplib
   smtp = smtplib.SMTP("smtp.gmail.com", 587)
   smtp.starttls()
   smtp.login("your-email@gmail.com", "your-app-password")
   smtp.quit()
   print("✅ Connection successful")
   ```

### Gmail Issues

- **"Less secure apps" blocked:** Use App Passwords instead
- **"Invalid credentials":** Verify you're using app-specific password, not Gmail password
- **"Timeout":** Gmail may be blocking repeated failed login attempts. Wait 30 minutes.

### SendGrid Issues

- **"Invalid API key":** Verify key starts with `SG.`
- **"Unauthorized":** Ensure API key has "Mail Send" permission
- **"Rate limited":** SendGrid free tier has sending limits

### AWS SES Issues

- **"MessageRejected":** Sender email not verified in SES
- **"ConfigurationSetDoesNotExist":** Region mismatch
- **"Throttling":** In sandbox mode, emails must be to verified addresses

---

## Production Checklist

- [ ] Choose email provider (SMTP/SendGrid/AWS SES)
- [ ] Set environment variables in production
- [ ] Test email sending with real recipient
- [ ] Configure quiet hours for your team
- [ ] Monitor Celery workers for email queue
- [ ] Set up alerting for failed email sends
- [ ] Document your email provider choice for team
- [ ] Test email templates are rendering correctly

---

## Support

For SMTP issues: https://www.smtp.com/
For SendGrid: https://docs.sendgrid.com/
For AWS SES: https://docs.aws.amazon.com/ses/
