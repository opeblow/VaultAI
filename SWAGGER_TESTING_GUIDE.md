# Swagger Testing Guide

## Screenshots

The following screenshots demonstrate the Swagger UI interface and workflow:

![Screenshot 1 - Overview](screenshots/WhatsApp%20Image%202026-04-24%20at%2012.27.25.jpeg)
*Swagger UI main interface showing available API endpoints*

![Screenshot 2 - Authentication](screenshots/WhatsApp%20Image%202026-04-24%20at%2012.27.48.jpeg)
*Authentication section for registering and logging in users*

![Screenshot 3 - Authorization](screenshots/WhatsApp%20Image%202026-04-24%20at%2012.28.08.jpeg)
*Authorization modal for pasting the bearer token*

![Screenshot 4 - Upload](screenshots/WhatsApp%20Image%202026-04-24%20at%2012.28.27.jpeg)
*Audio upload endpoint for ingesting podcast content*

![Screenshot 5 - Query](screenshots/WhatsApp%20Image%202026-04-24%20at%2012.28.46.jpeg)
*Query endpoint for asking AI questions about podcast content*

---

## Step-by-Step Swagger Testing Guide

### Step 1: Register
- **Endpoint:** `POST /auth/register`
- **Description:** Register a new user account

### Step 2: Login
- **Endpoint:** `POST /auth/login`
- **Description:** Log in with your credentials
- **Action:** Copy the authentication token returned from the response

### Step 3: Authorize
- **Description:** Click the **Authorize** button at the top of Swagger UI
- **Action:** Paste the bearer token into the input field

### Step 4: Upload Audio
- **Endpoint:** `POST /ingest/upload`
- **Description:** Upload audio content for processing

### Step 5: Check Job Status
- **Endpoint:** `GET /ingest/jobs/{job_id}`
- **Description:** Check the status of an uploaded audio job

### Step 6: Ask AI
- **Endpoint:** `POST /query/ask`
- **Description:** Ask AI questions about the processed podcast content

### Step 7: List Vaults
- **Endpoint:** `GET /vaults/`
- **Description:** List all available podcast vaults

### Step 8: Get Summary
- **Endpoint:** `GET /vaults/{podcast_id}/summary`
- **Description:** Retrieve the summary of a specific podcast

---

## Paystack Webhook Testing

### Testing Paystack Payment Webhook
- **Endpoint:** `POST /payments/webhook`
- **Description:** Test the Paystack payment webhook integration

#### Steps:
1. Click on the `POST /payments/webhook` endpoint
2. Click **Try it out**
3. Paste the test payload into the request body
4. Click **Execute**
5. **Expected Response:** Confirmation that the user's plan was upgraded successfully