import os
import time
import base64
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cashfree Sandbox base URL
BASE_URL = "https://payout-gamma.cashfree.com"

CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET")
PUBLIC_KEY_PATH = os.getenv("CASHFREE_PUBLIC_KEY_PATH")  # Path to your .pem file


def generate_signature() -> str | None:
    """
    Generate RSA signature using the public key for 2FA.
    Formula: RSA_ENCRYPT( clientId + "." + unix_timestamp )
    Signature is valid for 10 minutes.
    """
    if not PUBLIC_KEY_PATH or not os.path.exists(PUBLIC_KEY_PATH):
        logger.warning("No public key path set or file not found — skipping signature (IP whitelist mode)")
        return None

    try:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_OAEP

        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key = RSA.import_key(f.read())

        data_to_encrypt = f"{CLIENT_ID}.{int(time.time())}"
        cipher = PKCS1_OAEP.new(public_key)
        encrypted = cipher.encrypt(data_to_encrypt.encode("utf-8"))
        signature = base64.b64encode(encrypted).decode("utf-8")

        logger.info("Signature generated successfully")
        return signature

    except Exception as e:
        logger.error(f"Signature generation failed: {e}")
        return None


def _build_auth_headers() -> dict:
    """Build headers for Cashfree API — with signature if public key is configured."""
    headers = {
        "X-Client-Id": CLIENT_ID,
        "X-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    signature = generate_signature()
    if signature:
        headers["X-Cf-Signature"] = signature
    return headers


def get_auth_token() -> str | None:
    """Authenticate with Cashfree and return a Bearer token."""
    url = f"{BASE_URL}/payout/v1/authorize"
    try:
        response = requests.post(url, headers=_build_auth_headers())
        data = response.json()
        logger.info(f"Auth response: {data}")

        if data.get("status") == "SUCCESS":
            return data["data"]["token"]
        else:
            logger.error(f"Auth failed: {data}")
            return None
    except Exception as e:
        logger.error(f"Auth exception: {e}")
        return None


def create_beneficiary(token: str, bene_id: str, name: str, bank_account: str, ifsc: str) -> str:
    """
    Add a beneficiary to Cashfree.
    Returns 'SUCCESS', 'ALREADY_EXISTS', or an error message.
    """
    url = f"{BASE_URL}/payout/v1/addBeneficiary"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "beneId": bene_id,
        "name": name,
        "email": "vendor@example.com",     # Required by Cashfree, placeholder OK for sandbox
        "phone": "9999999999",             # Required by Cashfree, placeholder OK for sandbox
        "bankAccount": bank_account,
        "ifsc": ifsc,
        "address1": "Vendor Address",      # Required by Cashfree
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        logger.info(f"Create beneficiary response: {data}")

        if data.get("status") == "SUCCESS":
            return "SUCCESS"
        elif data.get("subCode") == "409":
            return "ALREADY_EXISTS"
        else:
            return data.get("message", "UNKNOWN_ERROR")
    except Exception as e:
        logger.error(f"Create beneficiary exception: {e}")
        return str(e)


def make_transfer(token: str, transfer_id: str, bene_id: str, amount: float) -> dict:
    """Initiate a payout transfer."""
    url = f"{BASE_URL}/payout/v1/requestTransfer"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": str(amount),
        "transferId": transfer_id,
        "transferMode": "banktransfer",
        "beneId": bene_id,
        "remarks": "Vendor payment via Telegram Bot",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        logger.info(f"Transfer response: {data}")
        return {
            "status": data.get("status", "UNKNOWN"),
            "message": data.get("message", ""),
            "raw": data
        }
    except Exception as e:
        logger.error(f"Transfer exception: {e}")
        return {"status": "ERROR", "message": str(e)}


def get_transfer_status(token: str, transfer_id: str) -> dict:
    """Check the status of a transfer."""
    url = f"{BASE_URL}/payout/v1/getTransferStatus"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {"transferId": transfer_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        logger.info(f"Transfer status response: {data}")
        transfer_data = data.get("data", {}).get("transfer", {})
        return {
            "status": transfer_data.get("status", data.get("status", "UNKNOWN")),
            "message": data.get("message", ""),
            "raw": data
        }
    except Exception as e:
        logger.error(f"Transfer status exception: {e}")
        return {"status": "ERROR", "message": str(e)}


def validate_bank_account(ifsc: str) -> tuple[bool, dict]:
    """
    Validate IFSC code using the free RBI/Razorpay IFSC API.
    Returns (True, bank_info_dict) if valid, (False, {}) if not found.
    """
    try:
        url = f"https://ifsc.razorpay.com/{ifsc}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {}
    except Exception as e:
        logger.error(f"IFSC validation error: {e}")
        # If the validation API is down, allow it through to avoid blocking payments
        return True, {"BANK": "Unknown (validation service unavailable)"}