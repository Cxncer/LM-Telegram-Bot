import os
import requests
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from telegram.error import TelegramError

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variable
TOKEN = os.getenv('TOKEN')
VERCEL_URL = os.getenv('VERCEL_URL')  # Add this to your .env (your Vercel app URL)

# Ensure the token is set
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# Set up Flask
app = Flask(__name__)

# Initialize the Telegram bot application
application = Application.builder().token(TOKEN).build()

# Define states for the conversation
CUSTOMER_NAME, ORDER_ITEM, PRICE, QUANTITY = range(4)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome to Lomorng Aroma by Sam! Please enter the Customer Name:"
    )
    context.user_data['state'] = CUSTOMER_NAME
    return CUSTOMER_NAME

async def customer_name(update: Update, context: CallbackContext):
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the Order Item:")
    context.user_data['state'] = ORDER_ITEM
    return ORDER_ITEM

async def order_item(update: Update, context: CallbackContext):
    context.user_data['order_item'] = update.message.text
    await update.message.reply_text("Great! Please enter the Price:")
    context.user_data['state'] = PRICE
    return PRICE

async def price(update: Update, context: CallbackContext):
    context.user_data['price'] = update.message.text
    await update.message.reply_text("Almost done! Please enter the Quantity:")
    context.user_data['state'] = QUANTITY
    return QUANTITY

async def quantity(update: Update, context: CallbackContext):
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
            f"Order Summary\n"
            f" - Customer Name: {context.user_data['customer_name']}\n"
            f" - Order Item:    {context.user_data['order_item']}\n"
            f" - Price:         {context.user_data['price']}\n"
            f" - Quantity:      {context.user_data['quantity']}\n"
            f" - Total Price:   {context.user_data['total_price']}"
        )
        
        await update.message.reply_text(order_summary)
        context.user_data['state'] = None  # Reset state

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid quantity.")
        return QUANTITY

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Order creation cancelled.")
    context.user_data['state'] = None  # Reset state
    return ConversationHandler.END

# Flask route to handle webhook updates
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)  # Put the update in the queue for processing
    return 'ok', 200

# Set up webhook with Telegram
def set_webhook():
    webhook_url = f"{VERCEL_URL}/{TOKEN}"  # Your Vercel deployment URL
    url = f'https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}'
    response = requests.get(url)
    print(response.json())  # Check the response to ensure webhook is set

# Delete any existing webhook
def delete_webhook():
    url = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook'
    response = requests.get(url)
    print(response.json())  # Print response to verify successful webhook deletion

# Main function to set the webhook and start the Flask app
if __name__ == '__main__':
    delete_webhook()  # Clean up any previous webhooks
    set_webhook()     # Set the new webhook
    app.run(debug=True, port=5000)  # Run the Flask app
