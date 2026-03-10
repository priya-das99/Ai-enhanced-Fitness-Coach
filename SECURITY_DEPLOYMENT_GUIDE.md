# Security Deployment Guide

## Problem Fixed
Users were staying logged in across different browsers/devices because:
1. **Shared Secret Key**: All deployments used the same JWT secret key
2. **No Server-side Session Management**: Logout only cleared client-side tokens
3. **Long Token Expiration**: 30-minute tokens were too long-lived
4. **No Token Blacklisting**: Revoked tokens could still be used

## Solutions Implemented

### 1. Unique Secret Key Generation
- Generated a cryptographically secure secret key
- Updated `.env` file with the new key
- **CRITICAL**: Each deployment must have its own unique secret key

### 2. Token Blacklisting System
- Added `TokenService` for server-side token management
- Tokens are blacklisted on logout and checked on each request
- Expired blacklisted tokens are automatically cleaned up

### 3. Reduced Token Expiration
- Changed from 30 minutes to 15 minutes
- Shorter-lived tokens reduce security risk

### 4. Enhanced JWT Tokens
- Added unique JWT ID (JTI) to each token
- Enables proper token tracking and revocation

## Deployment Steps

### For Local Development
1. **Generate New Secret Key** (already done):
   ```bash
   cd backend
   python generate_secret_key.py
   ```

2. **Update Environment**:
   - The `.env` file has been updated with a new secret key
   - Token expiration reduced to 15 minutes

3. **Test the Fix**:
   ```bash
   # Start the backend
   cd backend
   python -m uvicorn app.main:app --reload

   # In another terminal, run the security test
   python test_session_security.py
   ```

### For Production Deployment

#### Step 1: Generate Production Secret Key
```bash
# On your production server
cd backend
python generate_secret_key.py
```

#### Step 2: Update Production Environment
Set these environment variables in your production environment:
```bash
SECRET_KEY=<your-generated-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

#### Step 3: Deploy Updated Code
Deploy the updated backend code with:
- Updated `app/core/security.py`
- New `app/services/token_service.py`
- Updated `app/api/deps.py`
- Updated `app/api/v1/endpoints/auth.py`
- Updated `app/scheduler.py`

#### Step 4: Database Migration
The token blacklist database will be created automatically on first use.

## Verification

### Test 1: Session Isolation
1. Login from Browser A
2. Login from Browser B with different user
3. Verify each browser shows the correct user
4. Logout from Browser A
5. Verify Browser A is logged out but Browser B remains logged in

### Test 2: Token Revocation
1. Login and get a token
2. Use the token to access protected endpoints (should work)
3. Logout
4. Try to use the same token again (should fail with 401)

### Test 3: Token Expiration
1. Login and note the token expiration time
2. Verify tokens expire in 15 minutes or less
3. Verify expired tokens are rejected

## Security Best Practices

### For Production
1. **Never reuse secret keys** between environments
2. **Use HTTPS** for all authentication endpoints
3. **Monitor token usage** and watch for suspicious patterns
4. **Regular key rotation** (consider rotating secret keys periodically)
5. **Rate limiting** on login endpoints to prevent brute force attacks

### Environment Variables
```bash
# Required for production
SECRET_KEY=<unique-cryptographically-secure-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Optional but recommended
ALLOWED_ORIGINS=https://yourdomain.com
```

## Monitoring

The system now logs:
- Token blacklisting events
- Failed authentication attempts due to blacklisted tokens
- Token cleanup operations

Monitor these logs for security insights.

## Rollback Plan

If issues occur, you can temporarily:
1. Increase `ACCESS_TOKEN_EXPIRE_MINUTES` back to 30
2. The blacklisting system is backward compatible
3. Old tokens will still work until they expire naturally

## Files Modified

- `backend/.env` - New secret key and token expiration
- `backend/app/core/security.py` - JWT with JTI support
- `backend/app/services/token_service.py` - New token blacklisting service
- `backend/app/api/deps.py` - Blacklist checking in auth dependency
- `backend/app/api/v1/endpoints/auth.py` - Proper logout with token revocation
- `backend/app/scheduler.py` - Token cleanup job
- `backend/generate_secret_key.py` - Secret key generator utility
- `backend/test_session_security.py` - Security testing script

## Next Steps

1. **Deploy to production** with unique secret key
2. **Test thoroughly** in production environment
3. **Monitor logs** for any authentication issues
4. **Consider implementing** refresh tokens for better UX
5. **Add rate limiting** for additional security