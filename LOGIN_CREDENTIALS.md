# SME Costing Copilot - Login Credentials & Access Guide

## 🎉 Test User Created Successfully!

### Test User Credentials
```
Email:    test@example.com
Password: TestPass123
Role:     Owner (Full System Access)
```

## 🌐 Access URLs

### Local Development
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Production (Deployed)
- **Frontend (Vercel)**: https://sme-costing-copilot-frontend.vercel.app
- **Backend (Railway)**: Check your Railway dashboard for the URL

## 📝 Login Instructions

### For Localhost (http://localhost:3000)
1. Open http://localhost:3000 in your browser
2. Click "Sign in" (or you'll see the login page directly)
3. Enter email: `test@example.com`
4. Enter password: `TestPass123`
5. Click "Sign in"
6. You'll be redirected to the dashboard

### For Vercel (Production)
1. Wait for Vercel deployment to complete (check: https://vercel.com/dashboard)
2. Open https://sme-costing-copilot-frontend.vercel.app
3. Use the same credentials as above
4. Make sure your Railway backend is deployed and the URL is correct

## 🔧 What Was Fixed

### Frontend Error Handling
- ✅ Fixed "[object Object]" error display
- ✅ Now properly shows FastAPI validation error messages
- ✅ Added password requirements hint on registration page
- ✅ Improved error messages for both login and registration

### Password Requirements
When registering new users, passwords must:
- Be at least 8 characters long
- Contain at least one uppercase letter (A-Z)
- Contain at least one lowercase letter (a-z)
- Contain at least one digit (0-9)

Example valid passwords:
- `TestPass123`
- `Admin123!@#`
- `MyPassword1`

### Backend Configuration
- ✅ CORS configured for both localhost and Vercel
- ✅ Backend running on http://localhost:8000
- ✅ All Phase 3 features available

## 🚀 Available Features

With the Owner role, you have full access to:

1. **Authentication & Authorization**
   - User registration and login
   - Role-based access control (RBAC)
   - JWT token authentication

2. **Client Management**
   - Create and manage clients
   - Track client information

3. **Product Management**
   - Add and manage products
   - Track product details

4. **Order Evaluation**
   - Evaluate order profitability
   - Calculate margins and costs

5. **Financial Management**
   - Track receivables and payables
   - Monitor cash flow
   - Financial reporting

6. **Scenario Analysis**
   - Create what-if scenarios
   - Compare different business scenarios

7. **AI Assistant**
   - Get AI-powered insights
   - Ask questions about your data

8. **Integrations**
   - Connect with external systems
   - Sync data

9. **Notifications**
   - Email notifications
   - Digest emails
   - Alert preferences

10. **Reports**
    - Generate Excel and CSV reports
    - Schedule automated reports
    - Export financial data

11. **Audit Logs**
    - Track all system activities
    - View audit trails

## 🔍 Testing the System

### Quick Test Flow
1. Login with test credentials
2. Navigate to Clients → Create a new client
3. Navigate to Products → Add a product
4. Navigate to Evaluations → Evaluate an order
5. Check the dashboard for insights

### API Testing (Optional)
You can also test the API directly using the Swagger UI:
1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Login to get a token, then use it for other endpoints

## 🐛 Troubleshooting

### If login fails on localhost:
1. Make sure both servers are running:
   - Backend: http://localhost:8000/health should return `{"status": "healthy"}`
   - Frontend: http://localhost:3000 should load
2. Check browser console for errors (F12)
3. Try clearing browser cache and localStorage
4. Make sure you're using the correct password: `TestPass123` (case-sensitive)

### If login fails on Vercel:
1. Check that Railway backend is deployed and running
2. Verify CORS_ORIGINS in Railway environment includes your Vercel URL
3. Check Railway logs for errors
4. Make sure the test user exists in the production database
   - You may need to run `create_test_user.py` on Railway

### If you see validation errors:
- Make sure password meets requirements (uppercase, lowercase, digit, 8+ chars)
- Check that all required fields are filled
- Error messages should now display clearly (not "[object Object]")

## 📦 Recent Changes Deployed

**Commit: 38f4d73**
- Fixed frontend error handling for better error messages
- Added password requirements hint
- Created test user with proper credentials
- Improved login/registration error display

**Commit: 793ab9a**
- Completed Tier 4 tasks (Excel/CSV parsers with round-trip tests)
- Updated CORS configuration
- Fixed main.py imports

## 🎯 Next Steps

1. **Test the login** on localhost with the provided credentials
2. **Wait for deployments** to complete on Railway and Vercel
3. **Test on production** once deployments are done
4. **Create additional users** if needed (use the registration page)
5. **Explore the features** and provide feedback

## 📞 Need Help?

If you encounter any issues:
1. Check the troubleshooting section above
2. Check browser console for errors (F12 → Console tab)
3. Check backend logs in the terminal
4. Provide specific error messages for faster debugging

---

**Status**: ✅ Ready to use on localhost
**Production Status**: ⏳ Waiting for Railway/Vercel deployment
