# Email Service Integration Guide

Quick reference for integrating the production-ready email service into existing workers.

## Quick Start

### 1. Setup Configuration

Add to `.env`:

```bash
# Choose one provider:

# Option A: SMTP (Gmail recommended)
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=noreply@truematch.ai
SMTP_PASSWORD=your-app-specific-password
EMAIL_FROM_ADDRESS=noreply@truematch.ai

# Option B: SendGrid
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM_ADDRESS=noreply@truematch.ai

# Option C: AWS SES
EMAIL_PROVIDER=ses
AWS_REGION=us-east-1
EMAIL_FROM_ADDRESS=noreply@truematch.ai
```

### 2. Integration in Workers

#### In Auto-Approve Worker

```python
from app.workers.candidate_notification import CandidateNotificationWorker
from app.core.email_service import EmailService

# In auto_approve.py _approve_queue_item method

# Send approval notification (async, non-blocking)
worker = CandidateNotificationWorker(self.db)
success = await worker.notify_assessment_approved(
    assessment_id=assessment_id,
    candidate_email=candidate.email,
    candidate_name=candidate.name,
    position_title=assessment.position.title,
    company_name=assessment.position.company.name,
    recruiter_name="Hiring Team",
    recruiter_email="hiring@company.com",
    strengths=assessment.capability_summary[:3],
)

if success:
    logger.info(f"Approval notification sent to {candidate.email}")
else:
    logger.error(f"Failed to send approval notification to {candidate.email}")
```

#### In Auto-Reject Worker

```python
from app.workers.candidate_notification import CandidateNotificationWorker

# In auto_reject.py _reject_queue_item method

# Send rejection notification (async, non-blocking)
if resume and resume.candidate_email:
    worker = CandidateNotificationWorker(self.db)
    success = await worker.notify_assessment_rejected(
        assessment_id=assessment_id,
        candidate_email=resume.candidate_email,
        candidate_name=resume.candidate_name,
        position_title=assessment.position.title,
        company_name=assessment.position.company.name,
        recruiter_name="Hiring Team",
        recruiter_email="hiring@company.com",
        rejection_reason="Assessment score below minimum threshold",
    )
    
    if success:
        logger.info(f"Rejection notification sent to {resume.candidate_email}")
```

#### In Assessment Start Endpoint

```python
from app.workers.candidate_notification import CandidateNotificationWorker

@router.post("/assessments/start")
async def start_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # ... assessment setup logic ...
    
    # Send candidate notification
    worker = CandidateNotificationWorker(db)
    await worker.notify_assessment_started(
        assessment_id=assessment_id,
        candidate_email=candidate.email,
        candidate_name=candidate.name,
        position_title=position.title,
        company_name=position.company.name,
        assessment_url=f"https://app.truematch.ai/assess/{assessment_id}",
        recruiter_name=recruiter.name,
        recruiter_email=recruiter.email,
    )
    
    return {"status": "Assessment started"}
```

### 3. Monitor Email Logs

```python
from sqlalchemy import select
from app.models.notification import EmailLog

# Get all sent emails
stmt = select(EmailLog).where(EmailLog.status == "sent")
result = await db.execute(stmt)
sent_emails = result.scalars().all()

# Get failed emails
stmt = select(EmailLog).where(EmailLog.status == "failed")
result = await db.execute(stmt)
failed_emails = result.scalars().all()

# Get emails for specific assessment
stmt = select(EmailLog).where(EmailLog.assessment_id == assessment_id)
result = await db.execute(stmt)
emails = result.scalars().all()

# Print results
for email in failed_emails:
    print(f"{email.recipient_email}: {email.error_message}")
```

## Common Scenarios

### Scenario 1: Assessment Auto-Approved

```
1. AssessmentCompleted event → score >= AUTO_APPROVE_THRESHOLD
2. Auto-Approve Worker processes assessment
3. Queue item marked APPROVED
4. CandidateNotificationWorker.notify_assessment_approved() called
5. EmailService renders template
6. Email sent via configured provider
7. Status logged to email_logs table
8. Recruiter sees updated queue item in dashboard
9. Candidate receives approval email
```

### Scenario 2: Assessment Auto-Rejected

```
1. AssessmentCompleted event → score < AUTO_REJECT_THRESHOLD
2. Auto-Reject Worker processes assessment
3. Queue item marked REJECTED
4. CandidateNotificationWorker.notify_assessment_rejected() called
5. EmailService renders template
6. Email sent via configured provider
7. Status logged to email_logs table
8. Recruiter sees updated queue item in dashboard
9. Candidate receives rejection email
```

### Scenario 3: Batch Candidate Notifications

```python
from app.core.email_service import EmailService, EmailTemplate

service = EmailService()

# Send welcome emails to multiple candidates
results = await service.send_batch_emails(
    recipients=[
        "candidate1@example.com",
        "candidate2@example.com",
        "candidate3@example.com",
    ],
    template_name=EmailTemplate.WELCOME,
    context_template={
        "profile_url": "https://app.truematch.ai/profile",
        "current_year": 2026,
    }
)

# Check results
for email, success in results.items():
    status = "✓ Sent" if success else "✗ Failed"
    print(f"{email}: {status}")
```

## Database Migration

If deploying to existing database, create the email_logs table:

```sql
-- Create email_logs table
CREATE TABLE email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_email VARCHAR(254) NOT NULL,
    template_name VARCHAR(50) NOT NULL,
    assessment_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'sent',
    subject VARCHAR(255) NOT NULL,
    error_message VARCHAR(500),
    provider VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Create indexes
CREATE INDEX ix_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX ix_email_logs_assessment_id ON email_logs(assessment_id);
CREATE INDEX ix_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX ix_email_logs_status ON email_logs(status);
CREATE INDEX ix_email_logs_template ON email_logs(template_name);
```

Or use Alembic migration:

```python
# alembic/versions/xxx_add_email_logs_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

def upgrade():
    op.create_table(
        'email_logs',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('recipient_email', sa.String(254), nullable=False),
        sa.Column('template_name', sa.String(50), nullable=False),
        sa.Column('assessment_id', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='sent'),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', JSONB, nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_email_logs_recipient', 'email_logs', ['recipient_email'])
    op.create_index('ix_email_logs_assessment_id', 'email_logs', ['assessment_id'])
    op.create_index('ix_email_logs_sent_at', 'email_logs', ['sent_at'])
    op.create_index('ix_email_logs_status', 'email_logs', ['status'])
    op.create_index('ix_email_logs_template', 'email_logs', ['template_name'])

def downgrade():
    op.drop_table('email_logs')
```

## Testing

### Unit Tests

```bash
# Run all email service tests
pytest tests/test_email_service.py -v

# Run specific test
pytest tests/test_email_service.py::TestEmailService::test_email_validation_valid -v

# Run with coverage
pytest tests/test_email_service.py --cov=app.core.email_service --cov=app.workers.candidate_notification
```

### Integration Test

```python
import asyncio
from app.core.email_service import EmailService, EmailTemplate
from app.config import settings

async def test_email_flow():
    service = EmailService(settings)
    
    # Test with real configuration
    success = await service.send_email(
        to_address="test@example.com",
        template_name=EmailTemplate.ASSESSMENT_STARTED,
        context={
            "candidate_name": "Test Candidate",
            "position_title": "Test Engineer",
            "company_name": "Test Company",
            "assessment_url": "https://example.com/assess",
            "recruiter_name": "Test Recruiter",
            "recruiter_email": "recruiter@example.com",
            "current_year": 2026,
        }
    )
    
    print(f"Send result: {success}")

# Run test
asyncio.run(test_email_flow())
```

### Manual Email Testing

```python
# In Python shell or test script
import asyncio
from app.core.email_service import EmailService, EmailTemplate
from app.config import settings

async def test():
    service = EmailService(settings)
    
    # Send test email
    result = await service.send_email(
        to_address="your-email@example.com",
        template_name=EmailTemplate.ASSESSMENT_APPROVED,
        context={
            "candidate_name": "Your Name",
            "position_title": "Software Engineer",
            "company_name": "Your Company",
            "recruiter_name": "Jane Smith",
            "recruiter_email": "jane@company.com",
            "strengths": ["Problem Solving", "Communication", "Teamwork"],
            "current_year": 2026,
        }
    )
    
    print(f"Email sent successfully!" if result else "Email send failed")

asyncio.run(test())
```

## Troubleshooting Checklist

- [ ] EMAIL_PROVIDER set to one of: "smtp", "sendgrid", "ses"
- [ ] EMAIL_FROM_ADDRESS is valid email
- [ ] SMTP credentials correct (username/password)
- [ ] SendGrid API key valid
- [ ] AWS credentials have SES permissions
- [ ] Email templates exist in `app/templates/email/`
- [ ] Database has `email_logs` table
- [ ] Logs show no template rendering errors
- [ ] Candidate email addresses are valid format
- [ ] Context dict has all template variables

## Performance Tips

1. **Use Batch Sending for Multiple Recipients**
   ```python
   # Good - non-blocking batch
   results = await service.send_batch_emails(recipients, template, context)
   
   # Avoid - blocking loop
   for recipient in recipients:
       await service.send_email(recipient, template, context)
   ```

2. **Defer to Background Task**
   ```python
   # In API endpoint - return immediately
   # Queue task for actual sending
   celery_app.send_task('send_notification', args=[assessment_id])
   ```

3. **Monitor Email Logs**
   ```python
   # Query failed emails periodically
   stmt = select(EmailLog).where(EmailLog.status == "failed")
   # Take action on failures
   ```

## Next Steps

1. Configure email provider in `.env`
2. Test with `pytest tests/test_email_service.py`
3. Integrate into auto_approve and auto_reject workers
4. Deploy migration for `email_logs` table
5. Monitor logs and email_logs table
6. Set up alerts for failed sends

## Support

For issues or questions:
1. Check EMAIL_SERVICE_IMPLEMENTATION.md for detailed docs
2. Review test examples in test_email_service.py
3. Check application logs for error details
4. Query email_logs table for delivery status

---

**Status:** Production-ready, Week 2 Tier 1 autonomous features unblocked
