import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cashfree Sandbox base URL
BASE_URL = "https://payout-gamma.cashfree.com"

CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET")


def get_auth_token() -> str | None:
    """Authenticate with Cashfree and return a Bearer token."""
    url = f"{BASE_URL}/payout/v1/authorize"
    headers = {
        "X-Client-Id": CLIENT_ID,
        "X-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers)
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
        "email": "vendor@example.com",       # Required by Cashfree, placeholder OK for sandbox
        "phone": "9999999999",               # Required by Cashfree, placeholder OK for sandbox
        "bankAccount": bank_account,
        "ifsc": ifsc,
        "address1": "Vendor Address",        # Required by Cashfree
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        logger.info(f"Create beneficiary response: {data}")

        if data.get("status") == "SUCCESS":
            return "SUCCESS"
        elif data.get("subCode") == "409":
            # Beneficiary already exists — that's fine
            return "ALREADY_EXISTS"
        else:
            return data.get("message", "UNKNOWN_ERROR")
    except Exception as e:
        logger.error(f"Create beneficiary exception: {e}")
        return str(e)


def make_transfer(token: str, transfer_id: str, bene_id: str, amount: float) -> dict:
    """
    Initiate a payout transfer.
    Returns the response dict with 'status' and 'message'.
    """
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
        "remarks": f"Vendor payment via Telegram Bot",
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
    """
    Check the status of a transfer by its ID.
    """
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