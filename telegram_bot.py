import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variable
TOKEN = os.getenv('TOKEN')

# Ensure the token is set
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# Function to delete any existing webhook
def delete_webhook(token):
    url = f'https://api.telegram.org/bot{token}/deleteWebhook'
    response = requests.get(url)
    print("Webhook Deletion Response:", response.json())  # Print response to verify successful webhook deletion

# Define states for the conversation
CUSTOMER_NAME, ORDER_ITEM, PRICE, QUANTITY = range(4)

async def start(update: Update, context):
    await update.message.reply_text(
        "Welcome! Let's create an order. Please enter the Customer Name:"
    )
    context.user_data['state'] = CUSTOMER_NAME
    return CUSTOMER_NAME

async def customer_name(update: Update, context):
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the Order Item:")
    context.user_data['state'] = ORDER_ITEM
    return ORDER_ITEM

async def order_item(update: Update, context):
    context.user_data['order_item'] = update.message.text
    await update.message.reply_text("Great! Please enter the Price:")
    context.user_data['state'] = PRICE
    return PRICE

async def price(update: Update, context):
    context.user_data['price'] = update.message.text
    await update.message.reply_text("Almost done! Please enter the Quantity:")
    context.user_data['state'] = QUANTITY
    return QUANTITY

async def quantity(update: Update, context):
    user_input = update.message.text.strip()

    if user_input.lower() == 'cancel':
        await cancel(update, context)
        return ConversationHandler.END

    try:
        quantity = int(user_input)
        context.user_data['quantity'] = quantity
        
        # Calculate the total price
        price = float(context.user_data['price'])
        quantity = int(context.user_data['quantity'])
        context.user_data['total_price'] = price * quantity
        
        # Recite the order details in one message
        order_summary = (
            f"Order Summary:\n"
            f"Customer Name: {context.user_data['customer_name']}\n"
            f"Order Item: {context.user_data['order_item']}\n"
            f"Price: {context.user_data['price']}\n"
            f"Quantity: {context.user_data['quantity']}\n"
            f"Total Price: {context.user_data['total_price']}"
        )
        
        await update.message.reply_text(order_summary)
        context.user_data['state'] = None  # Reset state

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid quantity.")
        return QUANTITY

async def cancel(update: Update, context):
    await update.message.reply_text("Order creation cancelled.")
    context.user_data['state'] = None  # Reset state
    return ConversationHandler.END

def main():
    # Delete any existing webhook
    delete_webhook(TOKEN)
    
    # Set up the application with polling
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
            ORDER_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_item)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    
    # Add handler for /start and /cancel commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel', cancel))
    
    application.run_polling()

if __name__ == '__main__':
    main()
