# Code Quality Maintenance Guide

## Overview

This guide outlines best practices for maintaining clean logging and code quality standards across the codebase.

## Standards Summary

### Do's ✓

#### Python (Backend)
```python
# Good: Use logger with proper level
import logging

logger = logging.getLogger(__name__)

logger.info("Processing completed")
logger.error("Error occurred", exc_info=True)
logger.warning("Potential issue detected")

# Good: Exception handling
try:
    perform_operation()
except OperationError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise  # Re-raise for caller to handle
```

#### JavaScript/TypeScript (Frontend)
```typescript
// Good: Use useToast() for user messages
const { addToast } = useToast();

try {
    const result = await fetchData();
    addToast('Data loaded successfully', 'success');
} catch (error) {
    console.error('Failed to load data:', error);
    addToast('Failed to load data', 'error');
}

// Good: Structured error handling
const handleSubmit = async (data: FormData) => {
    try {
        await saveData(data);
    } catch (error) {
        logger?.error('Save failed', error);
        setErrorMessage('Save failed');
    }
};
```

### Don'ts ✗

#### Python
```python
# Bad: Using print()
print("Processing started")  # NO

# Bad: Empty catch blocks
try:
    process()
except Exception:
    pass  # NO

# Bad: Emoji in logging
logger.info("🔧 Processing started")  # NO

# Bad: Commented-out code
# def old_function():
#     return sum([1, 2, 3])  # NO
```

#### JavaScript/TypeScript
```typescript
// Bad: Using console.log without context
console.log("Data received");  // NO (except for development)

// Bad: Emoji in logging
console.log('✅ Request completed');  // NO

// Bad: Empty catch blocks
try {
    await operation();
} catch (e) {
    // ignore  // NO
}

// Bad: Commented-out code
// const unused = calculateMetrics(data);  // NO
```

## Logging Levels Guide

### INFO
- Normal application flow
- Milestone events
- User actions

```python
logger.info(f"User {user_id} logged in")
logger.info("Database migration completed")
```

### WARNING
- Potentially problematic situations
- Deprecated feature usage
- Recoverable errors

```python
logger.warning(f"High memory usage: {usage}%")
logger.warning("Legacy API endpoint used")
```

### ERROR
- Error conditions that should be investigated
- Failed operations
- Exceptions in try/catch blocks

```python
logger.error(f"Failed to save data: {e}", exc_info=True)
logger.error("Database connection lost", extra={"retries": 3})
```

### CRITICAL
- System-level failures
- Security issues
- Data integrity problems

```python
logger.critical("Database corruption detected")
logger.critical("Security breach attempted", extra={"ip": client_ip})
```

### DEBUG
- Detailed diagnostic information
- Variable states
- Function entry/exit

```python
logger.debug(f"Processing item {item_id} with config {config}")
# Only use in development - should not appear in production logs
```

## File Organization Rules

### Module Structure
```
project/
├── app/
│   ├── core/
│   │   ├── logging.py          # Logging configuration
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── error_handlers.py   # Error handling logic
│   ├── models/                 # Data models
│   ├── services/               # Business logic
│   ├── api/                    # API routes
│   └── main.py                 # Entry point
└── tests/                      # Test files
```

### Logger Initialization
```python
# In each module, at the top level
logger = logging.getLogger(__name__)

# OR with custom name
logger = logging.getLogger("app.services.user")
```

## Common Patterns

### Request/Response Logging
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    response = await call_next(request)
    
    logger.info(
        f"Response: {response.status_code}",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
        }
    )
    
    return response
```

### Database Operations
```python
def save_user(user: User) -> bool:
    try:
        db.session.add(user)
        db.session.commit()
        logger.info(f"User {user.id} saved successfully")
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to save user {user.id}: {e}", exc_info=True)
        return False
```

### Error Handling in APIs
```python
@router.post("/data")
async def create_data(payload: DataSchema) -> Response:
    try:
        # Validation happens here
        data = await process_data(payload)
        logger.info(f"Data processed: {data.id}")
        return {"success": True, "data": data}
    
    except ValidationError as e:
        logger.warning(f"Validation failed: {e.errors()}")
        return {"success": False, "error": "Invalid input"}
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return {"success": False, "error": "Server error"}
    
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return {"success": False, "error": "Server error"}
```

## Testing Logging

### Capture Logs in Tests
```python
import logging

def test_user_login(caplog):
    """Test that login is properly logged."""
    with caplog.at_level(logging.INFO):
        result = login_user("user@example.com", "password")
    
    assert result.success
    assert "logged in" in caplog.text
```

### Mock Logger
```python
from unittest.mock import patch, MagicMock

def test_error_logging():
    """Test that errors are properly logged."""
    with patch('app.logger') as mock_logger:
        perform_operation()
        mock_logger.error.assert_called()
```

## Pre-commit Setup

### Install Hook
```bash
cp pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Test Hook
```bash
# This will run automatically on git commit
# To test manually:
./.git/hooks/pre-commit
```

## Code Review Checklist

When reviewing code, check for:

- [ ] No `print()` statements (use logger)
- [ ] No emoji in logging
- [ ] All exceptions are handled and logged
- [ ] No empty catch/except blocks
- [ ] No commented-out production code
- [ ] Logger properly initialized with `__name__`
- [ ] Appropriate log levels used
- [ ] Sensitive data not logged
- [ ] Error messages include context
- [ ] No circular logging (logger calling itself)

## Performance Considerations

### Lazy Logging
```python
# Bad: String concatenation even if not logged
logger.debug("Processing " + str(large_object))

# Good: String formatting (lazy evaluation)
logger.debug("Processing %s", large_object)

# Good: F-strings evaluated at call time
logger.debug(f"Processing {large_object}")
```

### Structured Logging
```python
# Bad: All info in message
logger.info(f"User {uid} from {ip} performed {action}")

# Good: Use extra for structured data
logger.info(
    "User action completed",
    extra={
        "user_id": uid,
        "ip_address": ip,
        "action": action,
    }
)
```

## Troubleshooting

### Missing Logs
1. Check logging level configuration
2. Verify logger name matches
3. Ensure handler is properly configured
4. Check log output destination

### Too Many Logs
1. Reduce DEBUG statements in production
2. Filter noisy modules
3. Implement log sampling
4. Review log retention policies

### Performance Issues
1. Profile logging overhead
2. Use lazy evaluation
3. Batch log writes
4. Consider async logging

## Resources

- Python logging docs: https://docs.python.org/3/library/logging.html
- 12-factor app logging: https://12factor.net/logs
- Structured logging: https://www.kartar.net/2015/12/structured-logging/

## Questions?

For questions or clarifications on these standards, consult:
1. The CLEANUP_REPORT.md for detailed changes
2. The cleanup_targeted.py script for automated checking
3. The pre-commit-hook.sh for automated prevention

---

Last Updated: 2026-07-23
Maintenance Owner: Engineering Team
