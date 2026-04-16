import logging
from app.utils.logger import setup_logger

logger = setup_logger("order_manager")

def run_single_test_trade(smart_api_obj):
    """
    Executes a single, strictly controlled manual trade for testing.
    Safety:
    - Hardcoded to SBIN-EQ, Qty 1, LIMIT order.
    - Requires explicit 'yes' confirmation from user.
    """
    if smart_api_obj is None:
        logger.error("No active session found. Cannot place order.")
        return

    # Strict safety parameters
    SYMBOL = "SBIN-EQ"
    TOKEN = "3045"
    EXCHANGE = "NSE"
    QUANTITY = 1
    ORDER_TYPE = "LIMIT"
    PRODUCT_TYPE = "DELIVERY"
    VARIETY = "NORMAL"
    TRANSACTION_TYPE = "BUY"
    DURATION = "DAY"

    print("\n" + "!"*40)
    print("WARNING: PREPARING REAL TRADE TEST")
    print("!"*40)
    
    try:
        # Prompt for Limit Price to make the order valid
        price_input = input(f"Enter LIMIT price for {SYMBOL} (Quantity: {QUANTITY}): ")
        limit_price = float(price_input)
        
        order_params = {
            "variety": VARIETY,
            "tradingsymbol": SYMBOL,
            "symboltoken": TOKEN,
            "transactiontype": TRANSACTION_TYPE,
            "exchange": EXCHANGE,
            "ordertype": ORDER_TYPE,
            "producttype": PRODUCT_TYPE,
            "duration": DURATION,
            "price": str(limit_price),
            "quantity": str(QUANTITY)
        }

        # Show detailed order summary
        print("\nORDER SUMMARY:")
        print(f"  Symbol:     {SYMBOL}")
        print(f"  Token:      {TOKEN}")
        print(f"  Exchange:   {EXCHANGE}")
        print(f"  Type:       {ORDER_TYPE}")
        print(f"  Side:       {TRANSACTION_TYPE}")
        print(f"  Quantity:   {QUANTITY}")
        print(f"  Price:      {limit_price}")
        print(f"  Product:    {PRODUCT_TYPE}")
        print("-" * 20)

        # FINAL SAFETY GUARD
        confirmation = input("\nAre you sure you want to place REAL order? (yes/no): ").strip().lower()
        
        if confirmation == "yes":
            logger.info(f"Placing REAL order for {SYMBOL} at {limit_price}...")
            order_id = smart_api_obj.placeOrder(order_params)
            logger.info(f"Order Placed Successfully! Order ID: {order_id}")
            print(f"\nSUCCESS: Order ID {order_id}")
        else:
            logger.warning("Order cancelled by user.")
            print("\nORDER CANCELLED. No trade was placed.")

    except ValueError:
        logger.error("Invalid price entered. Cancelled trade.")
        print("\nERROR: Invalid price format. Trade aborted.")
    except Exception as e:
        logger.error(f"Failed to place test order: {str(e)}")
        print(f"\nERROR: {str(e)}")

if __name__ == "__main__":
    print("Order Manager module loaded. This module should be called from the login session.")
