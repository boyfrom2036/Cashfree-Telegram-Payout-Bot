# Cashfree-Telegram-Payout-Bot
Automated vendor payment system using Telegram Bot and Cashfree Payout APIs for seamless bank transfers.

# 💸 Cashfree Telegram Payout Bot

A Telegram Bot that allows businesses to make vendor payments directly from Telegram using the Cashfree Payout API.

Instead of logging into a dashboard, users can simply enter vendor details through Telegram, and the bot securely initiates bank transfers via Cashfree.

## 🚀 Features

- 🤖 Telegram-based payment workflow
- 🏦 Vendor bank account transfers
- 🔐 Cashfree API authentication
- 👤 Beneficiary creation and management
- 💰 Instant payout initiation
- ✅ Input validation for:
  - Vendor Name
  - Bank Account Number
  - IFSC Code
  - Payment Amount
- 📋 Payment confirmation before transfer
- 📝 Local vendor storage for frequent payments
- 🔄 Transfer status tracking
- ⚡ Simple and lightweight Python implementation

---

## 🏗️ Project Architecture

```text
User
  │
  ▼
Telegram Bot
  │
  ▼
Cashfree Payout API
  │
  ▼
Beneficiary Creation
  │
  ▼
Bank Transfer Initiation
  │
  ▼
Payment Status Response
```

---

## 📂 Project Structure

```text
.
├── bot.py                 # Main Telegram bot
├── cashfree.py            # Cashfree API integration
├── vendors.py             # Vendor storage utility
├── requirements.txt       # Dependencies
├── .env                   # Environment variables
└── vendors.json           # Saved vendor records
```

---

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cashfree-telegram-payout-bot.git

cd cashfree-telegram-payout-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/Mac**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

CASHFREE_CLIENT_ID=YOUR_CASHFREE_CLIENT_ID
CASHFREE_CLIENT_SECRET=YOUR_CASHFREE_CLIENT_SECRET
```

---

## 🤖 Telegram Commands

### Start Bot

```text
/start
```

Displays welcome message and usage instructions.

### Make Payment

```text
/pay
```

Workflow:

1. Enter Vendor Name
2. Enter Bank Account Number
3. Enter IFSC Code
4. Enter Amount
5. Confirm Payment
6. Transfer Initiated

### Cancel Payment

```text
/cancel
```

Stops the current payment flow.

---

## 💳 Payment Flow

```text
/pay
   │
   ▼
Vendor Name
   │
   ▼
Bank Account
   │
   ▼
IFSC
   │
   ▼
Amount
   │
   ▼
Confirmation
   │
   ▼
Cashfree Authentication
   │
   ▼
Beneficiary Creation
   │
   ▼
Transfer Request
   │
   ▼
Success / Failure Response
```

---

## 🛡️ Input Validation

The bot validates:

### Account Number

- Numeric only
- Length between 9–18 digits

### IFSC Code

Example:

```text
SBIN0001234
```

### Amount

- Must be positive
- Decimal values supported

---

## 📦 Dependencies

- python-telegram-bot
- requests
- python-dotenv
- pycryptodome

Install:

```bash
pip install -r requirements.txt
```

---

## 🔒 Security Notes

- Never commit your `.env` file.
- Use Cashfree Sandbox credentials during testing.
- Rotate API keys periodically.
- Restrict bot access to authorized users in production.

---

## 🧪 Testing

This project is configured for the Cashfree Sandbox environment:

```python
BASE_URL = "https://payout-gamma.cashfree.com"
```

Before production deployment, update to the latest Cashfree production endpoints.

---

## 📈 Future Improvements

- Admin authentication
- Role-based access control
- Multi-user support
- Transaction history dashboard
- Database integration (PostgreSQL/MySQL)
- Export payment reports
- Web admin panel
- OTP/2FA approval workflow
- Audit logs

---

## 🎯 Use Cases

- Vendor Payments
- Freelancer Payouts
- Agency Operations
- SME Payment Automation
- Internal Finance Teams

---

## 👨‍💻 Author

Aman Kumar

AI Engineer | Automation Developer | Agentic AI Builder

LinkedIn: https://linkedin.com/in/yourprofile

---

## 📄 License

This project is licensed under the MIT License.

Feel free to use, modify, and distribute.
