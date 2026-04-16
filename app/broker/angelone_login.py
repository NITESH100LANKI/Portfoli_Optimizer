import os
import pyotp
from SmartApi import SmartConnect
from dotenv import load_dotenv
from app.utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

logger = setup_logger("angelone_broker")

def login():
    """
    Performs a secure login to Angel One SmartAPI using credentials from environment variables.
    Returns the SmartConnect session object and tokens if successful.
    """
    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    password = os.getenv("PASSWORD")
    totp_secret = os.getenv("TOTP_SECRET")

    # Safety check: Ensure all required credentials exist
    missing = []
    if not api_key: missing.append("API_KEY")
    if not client_id: missing.append("CLIENT_ID")
    if not password: missing.append("PASSWORD")
    if not totp_secret: missing.append("TOTP_SECRET")

    if missing:
        err_msg = f"Missing environment variables: {', '.join(missing)}"
        logger.error(err_msg)
        raise EnvironmentError(err_msg)

    try:
        logger.info(f"Initiating SmartAPI login for Client ID: {client_id}")
        
        # Generate 6-digit TOTP
        totp = pyotp.TOTP(totp_secret).now()
        
        # Initialize SmartConnect
        smart_api = SmartConnect(api_key=api_key)
        
        # Generate session
        data = smart_api.generateSession(client_id, password, totp)
        
        if data.get('status') is True:
            logger.info("Login Successful")
            return smart_api, data
        else:
            logger.error(f"Login failed: {data.get('message')}")
            return None, data

    except Exception as e:
        logger.error(f"An unexpected error occurred during login: {str(e)}")
        raise

if __name__ == "__main__":
    from app.broker.order_manager import run_single_test_trade
    
    # Standalone test block
    try:
        session, response = login()
        if session:
            print("Login Successful")
            
            # Hook for manual trade test
            # To run: python -m app.broker.angelone_login
            test_mode = input("\nDo you want to run a SAFE TRADE TEST? (yes/no): ").strip().lower()
            if test_mode == "yes":
                run_single_test_trade(session)
        else:
            print(f"Login Failed: {response.get('message')}")
    except Exception as e:
        print(f"Login Error: {str(e)}")
