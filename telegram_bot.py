import os
import requests
import asyncio
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from telegram.error import TelegramError
from threading import Thread

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variable
TOKEN = os.getenv('TOKEN')

# Ensure the token is set
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# Define states for the conversation
CUSTOMER_NAME, ORDER_ITEM, PRICE, QUANTITY = range(4)

# Flask app setup
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!'

@app.route('/webhook', methods=['POST'])
def webhook():
    json_update = request.get_json()
    update = Update.de_json(json_update, application.bot)
    application.update_queue.put(update)
    return 'ok'

# Delete any existing webhook
url = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook'
response = requests.get(url)
print(response.json())  # Print response to verify successful webhook deletion

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome! Let's create an order. Please enter the Customer Name:"
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

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Order creation cancelled.")
    context.user_data['state'] = None  # Reset state
    return ConversationHandler.END

async def main_bot_function():
    global application
    application = Application.builder().token(TOKEN).build()
    
    # Define the ConversationHandler
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
    
    # Add handlers to the application
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel', cancel))
    
    # Run the bot
    try:
        await application.run_polling()
    except TelegramError as e:
        print(f"Telegram Error: {e}")

def run_flask():
    app.run(host='0.0.0.0', port=80)

if __name__ == '__main__':
    # Start Flask app in a separate thread
    Thread(target=run_flask, daemon=True).start()
    
    # Run the bot in the main thread
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main_bot_function())
    except KeyboardInterrupt:
        pass
