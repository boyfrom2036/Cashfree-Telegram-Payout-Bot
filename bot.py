# import logging
# import os
# import re
# from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler,
#     ConversationHandler, ContextTypes, filters
# )
# from cashfree import get_auth_token, create_beneficiary, make_transfer, get_transfer_status
# from dotenv import load_dotenv

# load_dotenv()

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# # Conversation states
# NAME, BANK_ACCOUNT, IFSC, AMOUNT, CONFIRM = range(5)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         "👋 Welcome to *Cashfree Payout Bot*!\n\n"
#         "Use /pay to initiate a vendor payment.\n"
#         "Use /cancel to cancel anytime.",
#         parse_mode="Markdown"
#     )


# async def pay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data.clear()
#     await update.message.reply_text(
#         "💼 *New Vendor Payment*\n\nStep 1/4\nEnter the *vendor's full name*:",
#         parse_mode="Markdown",
#         reply_markup=ReplyKeyboardRemove()
#     )
#     return NAME


# async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     name = update.message.text.strip()
#     if len(name) < 2:
#         await update.message.reply_text("❌ Name is too short. Please enter a valid name:")
#         return NAME

#     context.user_data["name"] = name
#     await update.message.reply_text(
#         f"✅ Name: *{name}*\n\nStep 2/4\nEnter the *bank account number*:",
#         parse_mode="Markdown"
#     )
#     return BANK_ACCOUNT


# async def get_bank_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     account = update.message.text.strip()
#     if not re.match(r"^\d{9,18}$", account):
#         await update.message.reply_text("❌ Invalid account number. Must be 9–18 digits. Try again:")
#         return BANK_ACCOUNT

#     context.user_data["bank_account"] = account
#     await update.message.reply_text(
#         f"✅ Account: *{account}*\n\nStep 3/4\nEnter the *IFSC code* (e.g. SBIN0001234):",
#         parse_mode="Markdown"
#     )
#     return IFSC


# async def get_ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     ifsc = update.message.text.strip().upper()
#     if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc):
#         await update.message.reply_text("❌ Invalid IFSC code format. Try again (e.g. SBIN0001234):")
#         return IFSC

#     context.user_data["ifsc"] = ifsc
#     await update.message.reply_text(
#         f"✅ IFSC: *{ifsc}*\n\nStep 4/4\nEnter the *amount to pay* (in ₹, e.g. 500):",
#         parse_mode="Markdown"
#     )
#     return AMOUNT


# async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         amount = float(update.message.text.strip())
#         if amount <= 0:
#             raise ValueError
#     except ValueError:
#         await update.message.reply_text("❌ Invalid amount. Enter a positive number (e.g. 500):")
#         return AMOUNT

#     context.user_data["amount"] = amount
#     data = context.user_data

#     summary = (
#         f"📋 *Payment Summary*\n\n"
#         f"👤 Vendor Name : `{data['name']}`\n"
#         f"🏦 Account No  : `{data['bank_account']}`\n"
#         f"🔢 IFSC Code   : `{data['ifsc']}`\n"
#         f"💰 Amount      : ₹`{data['amount']:.2f}`\n\n"
#         f"Confirm payment?"
#     )

#     reply_keyboard = [["✅ Yes, Pay Now", "❌ Cancel"]]
#     await update.message.reply_text(
#         summary,
#         parse_mode="Markdown",
#         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
#     )
#     return CONFIRM


# async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     choice = update.message.text.strip()

#     if choice == "❌ Cancel":
#         await update.message.reply_text(
#             "❌ Payment cancelled.",
#             reply_markup=ReplyKeyboardRemove()
#         )
#         return ConversationHandler.END

#     data = context.user_data
#     await update.message.reply_text(
#         "⏳ Processing payment, please wait...",
#         reply_markup=ReplyKeyboardRemove()
#     )

#     try:
#         # Step 1: Get auth token
#         token = get_auth_token()
#         if not token:
#             await update.message.reply_text("❌ Failed to authenticate with Cashfree. Check your API keys.")
#             return ConversationHandler.END

#         # Step 2: Create a unique beneficiary ID
#         import hashlib, time
#         bene_id = "BENE_" + hashlib.md5(f"{data['bank_account']}{data['ifsc']}".encode()).hexdigest()[:12].upper()

#         # Step 3: Add beneficiary
#         bene_result = create_beneficiary(
#             token=token,
#             bene_id=bene_id,
#             name=data["name"],
#             bank_account=data["bank_account"],
#             ifsc=data["ifsc"]
#         )

#         if bene_result not in ["SUCCESS", "ALREADY_EXISTS"]:
#             await update.message.reply_text(f"❌ Failed to add beneficiary: {bene_result}")
#             return ConversationHandler.END

#         # Step 4: Make transfer
#         transfer_id = f"TRF_{int(time.time())}_{bene_id[-6:]}"
#         transfer_result = make_transfer(
#             token=token,
#             transfer_id=transfer_id,
#             bene_id=bene_id,
#             amount=data["amount"]
#         )

#         if transfer_result.get("status") in ["SUCCESS", "RECEIVED"]:
#             await update.message.reply_text(
#                 f"✅ *Payment Initiated Successfully!*\n\n"
#                 f"💰 ₹{data['amount']:.2f} → *{data['name']}*\n"
#                 f"🔖 Transfer ID: `{transfer_id}`\n\n"
#                 f"Use /status_{transfer_id} to check status.",
#                 parse_mode="Markdown"
#             )
#         else:
#             await update.message.reply_text(
#                 f"⚠️ Transfer response: `{transfer_result.get('message', 'Unknown error')}`",
#                 parse_mode="Markdown"
#             )

#     except Exception as e:
#         logger.error(f"Payment error: {e}")
#         await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

#     return ConversationHandler.END


# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data.clear()
#     await update.message.reply_text(
#         "❌ Operation cancelled. Use /pay to start again.",
#         reply_markup=ReplyKeyboardRemove()
#     )
#     return ConversationHandler.END


# async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text = update.message.text.strip()
#     if not text.startswith("/status_"):
#         await update.message.reply_text("Usage: /status_<transfer_id>")
#         return

#     transfer_id = text.replace("/status_", "").strip()
#     token = get_auth_token()
#     if not token:
#         await update.message.reply_text("❌ Auth failed.")
#         return

#     result = get_transfer_status(token, transfer_id)
#     status = result.get("status", "UNKNOWN")
#     emoji = {"SUCCESS": "✅", "PENDING": "⏳", "FAILED": "❌", "RECEIVED": "📨"}.get(status, "ℹ️")

#     await update.message.reply_text(
#         f"{emoji} Transfer `{transfer_id}`\nStatus: *{status}*",
#         parse_mode="Markdown"
#     )


# def main():
#     token = os.getenv("TELEGRAM_BOT_TOKEN")
#     if not token:
#         raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

#     app = ApplicationBuilder().token(token).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("pay", pay_start)],
#         states={
#             NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
#             BANK_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bank_account)],
#             IFSC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ifsc)],
#             AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
#             CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_payment)],
#         },
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(conv_handler)
#     app.add_handler(MessageHandler(filters.Regex(r"^/status_"), check_status))

#     print("🤖 Bot is running... Press Ctrl+C to stop.")
#     app.run_polling()


# if __name__ == "__main__":
#     main()


## new code

# import logging
# import os
# import re
# import hashlib
# import time
# from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler,
#     ConversationHandler, ContextTypes, filters, CallbackQueryHandler
# )
# from cashfree_public import get_auth_token, create_beneficiary, make_transfer, get_transfer_status, validate_bank_account
# from vendors import save_vendor, get_frequent_vendors
# from dotenv import load_dotenv

# load_dotenv()

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# # Conversation states
# CHOOSE_VENDOR, ENTER_DETAILS, ENTER_AMOUNT, CONFIRM = range(4)


# # ─────────────────────────────────────────────
# #  /start
# # ─────────────────────────────────────────────
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         "👋 Welcome to *Cashfree Payout Bot*!\n\n"
#         "Commands:\n"
#         "💸 /pay — Make a vendor payment\n"
#         "📋 /history — View recent transfers\n"
#         "❌ /cancel — Cancel current operation",
#         parse_mode="Markdown"
#     )


# # ─────────────────────────────────────────────
# #  /pay — Step 1: Show frequent vendors or new
# # ─────────────────────────────────────────────
# async def pay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data.clear()
#     frequent = get_frequent_vendors(limit=5)

#     if frequent:
#         # Build inline keyboard with frequent vendors
#         buttons = []
#         for i, v in enumerate(frequent):
#             label = f"👤 {v['name']}  |  A/C: ...{v['bank_account'][-4:]}  |  {v['ifsc']}"
#             buttons.append([InlineKeyboardButton(label, callback_data=f"vendor_{i}")])
#         buttons.append([InlineKeyboardButton("➕ New Vendor", callback_data="vendor_new")])

#         context.user_data["frequent_vendors"] = frequent

#         await update.message.reply_text(
#             "💼 *Select a frequent vendor or add a new one:*",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup(buttons)
#         )
#         return CHOOSE_VENDOR
#     else:
#         # No vendors saved yet, go straight to entry
#         await prompt_new_vendor(update.message)
#         return ENTER_DETAILS


# async def prompt_new_vendor(message):
#     await message.reply_text(
#         "📝 *Enter vendor details in one message*, in this exact format:\n\n"
#         "`Name | Account Number | IFSC Code`\n\n"
#         "Example:\n"
#         "`Rajesh Kumar | 1234567890 | SBIN0001234`",
#         parse_mode="Markdown",
#         reply_markup=ReplyKeyboardRemove()
#     )


# # ─────────────────────────────────────────────
# #  Callback: vendor selected from inline list
# # ─────────────────────────────────────────────
# async def vendor_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     data = query.data

#     if data == "vendor_new":
#         await query.edit_message_text("➕ *Adding a new vendor...*", parse_mode="Markdown")
#         await query.message.reply_text(
#             "📝 *Enter vendor details in one message*, in this exact format:\n\n"
#             "`Name | Account Number | IFSC Code`\n\n"
#             "Example:\n"
#             "`Rajesh Kumar | 1234567890 | SBIN0001234`",
#             parse_mode="Markdown"
#         )
#         return ENTER_DETAILS

#     # Existing vendor selected
#     idx = int(data.replace("vendor_", ""))
#     vendors = context.user_data.get("frequent_vendors", [])
#     vendor = vendors[idx]

#     context.user_data["name"] = vendor["name"]
#     context.user_data["bank_account"] = vendor["bank_account"]
#     context.user_data["ifsc"] = vendor["ifsc"]

#     await query.edit_message_text(
#         f"✅ Selected: *{vendor['name']}*\n"
#         f"🏦 A/C: `{vendor['bank_account']}`  |  IFSC: `{vendor['ifsc']}`",
#         parse_mode="Markdown"
#     )
#     await query.message.reply_text(
#         "💰 Enter the *amount to pay* (₹):\n\nExample: `5000`",
#         parse_mode="Markdown"
#     )
#     return ENTER_AMOUNT


# # ─────────────────────────────────────────────
# #  Step 2a: Parse single-line vendor details
# # ─────────────────────────────────────────────
# async def enter_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text = update.message.text.strip()
#     parts = [p.strip() for p in text.split("|")]

#     if len(parts) != 3:
#         await update.message.reply_text(
#             "❌ Wrong format. Use exactly:\n\n"
#             "`Name | Account Number | IFSC Code`\n\n"
#             "Example: `Rajesh Kumar | 1234567890 | SBIN0001234`",
#             parse_mode="Markdown"
#         )
#         return ENTER_DETAILS

#     name, account, ifsc = parts[0], parts[1], parts[2].upper()

#     # Validate name
#     if len(name) < 2:
#         await update.message.reply_text("❌ Name is too short. Try again:")
#         return ENTER_DETAILS

#     # Validate account number
#     if not re.match(r"^\d{9,18}$", account):
#         await update.message.reply_text(
#             "❌ Invalid account number — must be 9 to 18 digits. Try again:",
#             parse_mode="Markdown"
#         )
#         return ENTER_DETAILS

#     # Validate IFSC format
#     if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc):
#         await update.message.reply_text(
#             "❌ Invalid IFSC format. It should look like `SBIN0001234`. Try again:",
#             parse_mode="Markdown"
#         )
#         return ENTER_DETAILS

#     # Validate IFSC exists via RBI API
#     await update.message.reply_text("🔍 Validating bank details, please wait...")
#     valid, bank_info = validate_bank_account(ifsc)
#     if not valid:
#         await update.message.reply_text(
#             f"❌ IFSC code `{ifsc}` not found in RBI records. Please double-check and try again.",
#             parse_mode="Markdown"
#         )
#         return ENTER_DETAILS

#     context.user_data["name"] = name
#     context.user_data["bank_account"] = account
#     context.user_data["ifsc"] = ifsc
#     context.user_data["bank_info"] = bank_info

#     bank_name = bank_info.get("BANK", "Unknown Bank")
#     branch = bank_info.get("BRANCH", "")
#     city = bank_info.get("CITY", "")

#     await update.message.reply_text(
#         f"✅ *Bank details verified!*\n\n"
#         f"🏦 Bank   : *{bank_name}*\n"
#         f"🌿 Branch : {branch}, {city}\n"
#         f"👤 Name   : `{name}`\n"
#         f"🔢 A/C    : `{account}`\n"
#         f"📍 IFSC   : `{ifsc}`\n\n"
#         f"💰 Now enter the *amount to pay* (₹):\n\nExample: `5000`",
#         parse_mode="Markdown"
#     )
#     return ENTER_AMOUNT


# # ─────────────────────────────────────────────
# #  Step 2b: Get amount
# # ─────────────────────────────────────────────
# async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         amount = float(update.message.text.strip().replace(",", ""))
#         if amount <= 0:
#             raise ValueError
#     except ValueError:
#         await update.message.reply_text("❌ Invalid amount. Enter a positive number like `5000`:", parse_mode="Markdown")
#         return ENTER_AMOUNT

#     context.user_data["amount"] = amount
#     d = context.user_data
#     bank_info = d.get("bank_info", {})
#     bank_name = bank_info.get("BANK", "—")

#     summary = (
#         f"📋 *Payment Summary*\n\n"
#         f"👤 Vendor  : `{d['name']}`\n"
#         f"🏦 Bank    : {bank_name}\n"
#         f"🔢 A/C No  : `{d['bank_account']}`\n"
#         f"📍 IFSC    : `{d['ifsc']}`\n"
#         f"💰 Amount  : ₹`{amount:,.2f}`\n\n"
#         f"Confirm payment?"
#     )

#     reply_keyboard = [["✅ Yes, Pay Now", "❌ Cancel"]]
#     await update.message.reply_text(
#         summary,
#         parse_mode="Markdown",
#         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
#     )
#     return CONFIRM


# # ─────────────────────────────────────────────
# #  Step 3: Confirm & Execute Payment
# # ─────────────────────────────────────────────
# async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     choice = update.message.text.strip()

#     if choice == "❌ Cancel":
#         await update.message.reply_text("❌ Payment cancelled.", reply_markup=ReplyKeyboardRemove())
#         return ConversationHandler.END

#     d = context.user_data
#     processing_msg = await update.message.reply_text(
#         "⏳ Processing payment...",
#         reply_markup=ReplyKeyboardRemove()
#     )

#     try:
#         # Auth
#         cf_token = get_auth_token()
#         if not cf_token:
#             await processing_msg.edit_text("❌ Cashfree authentication failed. Check your API keys.")
#             return ConversationHandler.END

#         # Beneficiary ID
#         bene_id = "BENE_" + hashlib.md5(f"{d['bank_account']}{d['ifsc']}".encode()).hexdigest()[:12].upper()

#         # Add beneficiary
#         bene_result = create_beneficiary(
#             token=cf_token,
#             bene_id=bene_id,
#             name=d["name"],
#             bank_account=d["bank_account"],
#             ifsc=d["ifsc"]
#         )
#         if bene_result not in ["SUCCESS", "ALREADY_EXISTS"]:
#             await processing_msg.edit_text(f"❌ Failed to register vendor: {bene_result}")
#             return ConversationHandler.END

#         # Transfer
#         transfer_id = f"TRF_{int(time.time())}_{bene_id[-6:]}"
#         result = make_transfer(
#             token=cf_token,
#             transfer_id=transfer_id,
#             bene_id=bene_id,
#             amount=d["amount"]
#         )

#         status = result.get("status", "UNKNOWN")

#         # Save vendor on any successful initiation
#         if status in ["SUCCESS", "RECEIVED"]:
#             save_vendor(d["name"], d["bank_account"], d["ifsc"])

#         # Build receipt
#         receipt = build_receipt(d, transfer_id, status, result)
#         await processing_msg.edit_text(receipt, parse_mode="Markdown")

#         # If status is RECEIVED (pending settlement), auto-poll after 10s
#         if status == "RECEIVED":
#             await update.message.reply_text(
#                 "🔄 Payment is being processed. I'll check the final status in a few seconds...",
#             )
#             time.sleep(8)
#             cf_token2 = get_auth_token()
#             if cf_token2:
#                 updated = get_transfer_status(cf_token2, transfer_id)
#                 final_status = updated.get("status", "UNKNOWN")
#                 final_receipt = build_receipt(d, transfer_id, final_status, updated, is_update=True)
#                 await update.message.reply_text(final_receipt, parse_mode="Markdown")

#     except Exception as e:
#         logger.error(f"Payment error: {e}")
#         await processing_msg.edit_text(f"❌ Unexpected error: {str(e)}")

#     return ConversationHandler.END


# def build_receipt(d: dict, transfer_id: str, status: str, result: dict, is_update: bool = False) -> str:
#     """Build a formatted payment receipt."""
#     status_map = {
#         "SUCCESS":  ("✅", "Payment Successful"),
#         "RECEIVED": ("📨", "Payment Initiated — Pending Settlement"),
#         "FAILED":   ("❌", "Payment Failed"),
#         "REVERSED": ("↩️", "Payment Reversed"),
#         "UNKNOWN":  ("❓", "Status Unknown"),
#     }
#     emoji, label = status_map.get(status, ("ℹ️", status))
#     prefix = "🔄 *Updated Receipt*" if is_update else "🧾 *Payment Receipt*"

#     raw = result.get("raw", {})
#     cf_ref = raw.get("data", {}).get("referenceId", "—")
#     utr = raw.get("data", {}).get("utr", "—")
#     failure_reason = raw.get("data", {}).get("reason", "")

#     receipt = (
#         f"{prefix}\n"
#         f"{'─' * 30}\n"
#         f"{emoji} *Status*       : {label}\n"
#         f"👤 *Vendor*       : `{d['name']}`\n"
#         f"🏦 *A/C Number*   : `{d['bank_account']}`\n"
#         f"📍 *IFSC*         : `{d['ifsc']}`\n"
#         f"💰 *Amount*       : ₹`{d['amount']:,.2f}`\n"
#         f"🔖 *Transfer ID*  : `{transfer_id}`\n"
#         f"📌 *CF Ref ID*    : `{cf_ref}`\n"
#         f"🏷 *UTR Number*   : `{utr}`\n"
#     )

#     if status == "FAILED" and failure_reason:
#         receipt += f"⚠️ *Failure Reason*: {failure_reason}\n"

#     receipt += (
#         f"{'─' * 30}\n"
#         f"💡 Use /history to see all transfers."
#     )
#     return receipt


# # ─────────────────────────────────────────────
# #  /history — Show recent transfer IDs
# # ─────────────────────────────────────────────
# async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     from vendors import get_all_vendors
#     vendors = get_all_vendors()
#     if not vendors:
#         await update.message.reply_text("No vendor history yet. Use /pay to get started.")
#         return

#     lines = ["📋 *Vendor Payment History*\n"]
#     for v in sorted(vendors, key=lambda x: x["last_paid"], reverse=True)[:10]:
#         lines.append(
#             f"👤 *{v['name']}*\n"
#             f"   A/C: `{v['bank_account']}` | IFSC: `{v['ifsc']}`\n"
#             f"   Paid {v['pay_count']} time(s) | Last: {v['last_paid'][:10]}\n"
#         )

#     await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# # ─────────────────────────────────────────────
# #  /cancel
# # ─────────────────────────────────────────────
# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data.clear()
#     await update.message.reply_text("❌ Cancelled. Use /pay to start again.", reply_markup=ReplyKeyboardRemove())
#     return ConversationHandler.END


# # ─────────────────────────────────────────────
# #  main
# # ─────────────────────────────────────────────
# def main():
#     token = os.getenv("TELEGRAM_BOT_TOKEN")
#     if not token:
#         raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

#     proxy_url = os.getenv("HTTPS_PROXY")
#     builder = ApplicationBuilder().token(token).connect_timeout(30).read_timeout(30).write_timeout(30)
#     if proxy_url:
#         builder = builder.proxy(proxy_url).get_updates_proxy(proxy_url)
#         print(f"🔀 Using proxy: {proxy_url}")

#     app = builder.build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("pay", pay_start)],
#         states={
#             CHOOSE_VENDOR: [CallbackQueryHandler(vendor_chosen)],
#             ENTER_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_details)],
#             ENTER_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
#             CONFIRM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_payment)],
#         },
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("history", history))
#     app.add_handler(conv_handler)

#     print("🤖 Bot is running... Press Ctrl+C to stop.")
#     app.run_polling()


# if __name__ == "__main__":
#     main()


## new code 1

import asyncio
import logging
import os
import re
import hashlib
import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters, CallbackQueryHandler
)
from cashfree_public import get_auth_token, create_beneficiary, make_transfer, get_transfer_status, validate_bank_account
from vendors import save_vendor, get_frequent_vendors
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSE_VENDOR, ENTER_DETAILS, ENTER_AMOUNT, CONFIRM = range(4)


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Cashfree Payout Bot*!\n\n"
        "Commands:\n"
        "💸 /pay — Make a vendor payment\n"
        "📋 /history — View recent transfers\n"
        "❌ /cancel — Cancel current operation",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────
#  /pay — Step 1: Show frequent vendors or new
# ─────────────────────────────────────────────
async def pay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    frequent = get_frequent_vendors(limit=5)

    if frequent:
        # Build inline keyboard with frequent vendors
        buttons = []
        for i, v in enumerate(frequent):
            label = f"👤 {v['name']}  |  A/C: ...{v['bank_account'][-4:]}  |  {v['ifsc']}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"vendor_{i}")])
        buttons.append([InlineKeyboardButton("➕ New Vendor", callback_data="vendor_new")])

        context.user_data["frequent_vendors"] = frequent

        await update.message.reply_text(
            "💼 *Select a frequent vendor or add a new one:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return CHOOSE_VENDOR
    else:
        # No vendors saved yet, go straight to entry
        await prompt_new_vendor(update.message)
        return ENTER_DETAILS


async def prompt_new_vendor(message):
    await message.reply_text(
        "📝 *Enter vendor details in one message*, in this exact format:\n\n"
        "`Name | Account Number | IFSC Code`\n\n"
        "Example:\n"
        "`Rajesh Kumar | 1234567890 | SBIN0001234`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )


# ─────────────────────────────────────────────
#  Callback: vendor selected from inline list
# ─────────────────────────────────────────────
async def vendor_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "vendor_new":
        await query.edit_message_text("➕ *Adding a new vendor...*", parse_mode="Markdown")
        await query.message.reply_text(
            "📝 *Enter vendor details in one message*, in this exact format:\n\n"
            "`Name | Account Number | IFSC Code`\n\n"
            "Example:\n"
            "`Rajesh Kumar | 1234567890 | SBIN0001234`",
            parse_mode="Markdown"
        )
        return ENTER_DETAILS

    # Existing vendor selected
    idx = int(data.replace("vendor_", ""))
    vendors = context.user_data.get("frequent_vendors", [])
    vendor = vendors[idx]

    context.user_data["name"] = vendor["name"]
    context.user_data["bank_account"] = vendor["bank_account"]
    context.user_data["ifsc"] = vendor["ifsc"]

    await query.edit_message_text(
        f"✅ Selected: *{vendor['name']}*\n"
        f"🏦 A/C: `{vendor['bank_account']}`  |  IFSC: `{vendor['ifsc']}`",
        parse_mode="Markdown"
    )
    await query.message.reply_text(
        "💰 Enter the *amount to pay* (₹):\n\nExample: `5000`",
        parse_mode="Markdown"
    )
    return ENTER_AMOUNT


# ─────────────────────────────────────────────
#  Step 2a: Parse single-line vendor details
# ─────────────────────────────────────────────
async def enter_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = [p.strip() for p in text.split("|")]

    if len(parts) != 3:
        await update.message.reply_text(
            "❌ Wrong format. Use exactly:\n\n"
            "`Name | Account Number | IFSC Code`\n\n"
            "Example: `Rajesh Kumar | 1234567890 | SBIN0001234`",
            parse_mode="Markdown"
        )
        return ENTER_DETAILS

    name, account, ifsc = parts[0], parts[1], parts[2].upper()

    # Validate name
    if len(name) < 2:
        await update.message.reply_text("❌ Name is too short. Try again:")
        return ENTER_DETAILS

    # Validate account number
    if not re.match(r"^\d{9,18}$", account):
        await update.message.reply_text(
            "❌ Invalid account number — must be 9 to 18 digits. Try again:",
            parse_mode="Markdown"
        )
        return ENTER_DETAILS

    # Validate IFSC format
    if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc):
        await update.message.reply_text(
            "❌ Invalid IFSC format. It should look like `SBIN0001234`. Try again:",
            parse_mode="Markdown"
        )
        return ENTER_DETAILS

    # Validate IFSC exists via RBI API
    await update.message.reply_text("🔍 Validating bank details, please wait...")
    valid, bank_info = validate_bank_account(ifsc)
    if not valid:
        await update.message.reply_text(
            f"❌ IFSC code `{ifsc}` not found in RBI records. Please double-check and try again.",
            parse_mode="Markdown"
        )
        return ENTER_DETAILS

    context.user_data["name"] = name
    context.user_data["bank_account"] = account
    context.user_data["ifsc"] = ifsc
    context.user_data["bank_info"] = bank_info

    bank_name = bank_info.get("BANK", "Unknown Bank")
    branch = bank_info.get("BRANCH", "")
    city = bank_info.get("CITY", "")

    await update.message.reply_text(
        f"✅ *Bank details verified!*\n\n"
        f"🏦 Bank   : *{bank_name}*\n"
        f"🌿 Branch : {branch}, {city}\n"
        f"👤 Name   : `{name}`\n"
        f"🔢 A/C    : `{account}`\n"
        f"📍 IFSC   : `{ifsc}`\n\n"
        f"💰 Now enter the *amount to pay* (₹):\n\nExample: `5000`",
        parse_mode="Markdown"
    )
    return ENTER_AMOUNT


# ─────────────────────────────────────────────
#  Step 2b: Get amount
# ─────────────────────────────────────────────
async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Enter a positive number like `5000`:", parse_mode="Markdown")
        return ENTER_AMOUNT

    context.user_data["amount"] = amount
    d = context.user_data
    bank_info = d.get("bank_info", {})
    bank_name = bank_info.get("BANK", "—")

    summary = (
        f"📋 *Payment Summary*\n\n"
        f"👤 Vendor  : `{d['name']}`\n"
        f"🏦 Bank    : {bank_name}\n"
        f"🔢 A/C No  : `{d['bank_account']}`\n"
        f"📍 IFSC    : `{d['ifsc']}`\n"
        f"💰 Amount  : ₹`{amount:,.2f}`\n\n"
        f"Confirm payment?"
    )

    reply_keyboard = [["✅ Yes, Pay Now", "❌ Cancel"]]
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM


# ─────────────────────────────────────────────
#  Step 3: Confirm & Execute Payment
# ─────────────────────────────────────────────
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "❌ Cancel":
        await update.message.reply_text("❌ Payment cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    d = context.user_data
    processing_msg = await update.message.reply_text(
        "⏳ Processing payment...",
        reply_markup=ReplyKeyboardRemove()
    )

    async def safe_reply(text, **kwargs):
        """Always sends a new message — never edits. Avoids BadRequest on edit."""
        await update.message.reply_text(text, **kwargs)

    try:
        # Auth
        cf_token = get_auth_token()
        if not cf_token:
            await safe_reply(
                "❌ *Cashfree authentication failed.*\n\n"
                "Your API keys are invalid. Please check:\n"
                "1️⃣ Open your `.env` file\n"
                "2️⃣ Make sure `CASHFREE_CLIENT_ID` and `CASHFREE_CLIENT_SECRET` are correct\n"
                "3️⃣ Make sure you're using *Sandbox* keys (not Production)\n"
                "4️⃣ Get keys from: Cashfree Dashboard → Payouts → Developers → API Keys",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        # Beneficiary ID
        bene_id = "BENE_" + hashlib.md5(f"{d['bank_account']}{d['ifsc']}".encode()).hexdigest()[:12].upper()

        # Add beneficiary
        bene_result = create_beneficiary(
            token=cf_token,
            bene_id=bene_id,
            name=d["name"],
            bank_account=d["bank_account"],
            ifsc=d["ifsc"]
        )
        if bene_result not in ["SUCCESS", "ALREADY_EXISTS"]:
            await safe_reply(f"❌ Failed to register vendor with Cashfree: `{bene_result}`", parse_mode="Markdown")
            return ConversationHandler.END

        # Transfer
        transfer_id = f"TRF_{int(time.time())}_{bene_id[-6:]}"
        result = make_transfer(
            token=cf_token,
            transfer_id=transfer_id,
            bene_id=bene_id,
            amount=d["amount"]
        )

        status = result.get("status", "UNKNOWN")

        # Save vendor on any successful initiation
        if status in ["SUCCESS", "RECEIVED"]:
            save_vendor(d["name"], d["bank_account"], d["ifsc"])

        # Build and send receipt as a new message
        receipt = build_receipt(d, transfer_id, status, result)
        await safe_reply(receipt, parse_mode="Markdown")

        # If status is RECEIVED (pending settlement), auto-poll after 8s
        if status == "RECEIVED":
            await safe_reply("🔄 Payment is processing. Checking final status in 8 seconds...")
            await asyncio.sleep(8)
            cf_token2 = get_auth_token()
            if cf_token2:
                updated = get_transfer_status(cf_token2, transfer_id)
                final_status = updated.get("status", "UNKNOWN")
                final_receipt = build_receipt(d, transfer_id, final_status, updated, is_update=True)
                await safe_reply(final_receipt, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Payment error: {e}")
        await safe_reply(f"❌ Unexpected error: `{str(e)}`", parse_mode="Markdown")

    return ConversationHandler.END


def build_receipt(d: dict, transfer_id: str, status: str, result: dict, is_update: bool = False) -> str:
    """Build a formatted payment receipt."""
    status_map = {
        "SUCCESS":  ("✅", "Payment Successful"),
        "RECEIVED": ("📨", "Payment Initiated — Pending Settlement"),
        "FAILED":   ("❌", "Payment Failed"),
        "REVERSED": ("↩️", "Payment Reversed"),
        "UNKNOWN":  ("❓", "Status Unknown"),
    }
    emoji, label = status_map.get(status, ("ℹ️", status))
    prefix = "🔄 *Updated Receipt*" if is_update else "🧾 *Payment Receipt*"

    raw = result.get("raw", {})
    cf_ref = raw.get("data", {}).get("referenceId", "—")
    utr = raw.get("data", {}).get("utr", "—")
    failure_reason = raw.get("data", {}).get("reason", "")

    receipt = (
        f"{prefix}\n"
        f"{'─' * 30}\n"
        f"{emoji} *Status*       : {label}\n"
        f"👤 *Vendor*       : `{d['name']}`\n"
        f"🏦 *A/C Number*   : `{d['bank_account']}`\n"
        f"📍 *IFSC*         : `{d['ifsc']}`\n"
        f"💰 *Amount*       : ₹`{d['amount']:,.2f}`\n"
        f"🔖 *Transfer ID*  : `{transfer_id}`\n"
        f"📌 *CF Ref ID*    : `{cf_ref}`\n"
        f"🏷 *UTR Number*   : `{utr}`\n"
    )

    if status == "FAILED" and failure_reason:
        receipt += f"⚠️ *Failure Reason*: {failure_reason}\n"

    receipt += (
        f"{'─' * 30}\n"
        f"💡 Use /history to see all transfers."
    )
    return receipt


# ─────────────────────────────────────────────
#  /history — Show recent transfer IDs
# ─────────────────────────────────────────────
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from vendors import get_all_vendors
    vendors = get_all_vendors()
    if not vendors:
        await update.message.reply_text("No vendor history yet. Use /pay to get started.")
        return

    lines = ["📋 *Vendor Payment History*\n"]
    for v in sorted(vendors, key=lambda x: x["last_paid"], reverse=True)[:10]:
        lines.append(
            f"👤 *{v['name']}*\n"
            f"   A/C: `{v['bank_account']}` | IFSC: `{v['ifsc']}`\n"
            f"   Paid {v['pay_count']} time(s) | Last: {v['last_paid'][:10]}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─────────────────────────────────────────────
#  /cancel
# ─────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled. Use /pay to start again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  main
# ─────────────────────────────────────────────
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    proxy_url = os.getenv("HTTPS_PROXY")
    builder = ApplicationBuilder().token(token).connect_timeout(30).read_timeout(30).write_timeout(30)
    if proxy_url:
        builder = builder.proxy(proxy_url).get_updates_proxy(proxy_url)
        print(f"🔀 Using proxy: {proxy_url}")

    app = builder.build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("pay", pay_start)],
        states={
            CHOOSE_VENDOR: [CallbackQueryHandler(vendor_chosen)],
            ENTER_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_details)],
            ENTER_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            CONFIRM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(conv_handler)

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()