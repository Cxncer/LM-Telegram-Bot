import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext, CallbackQueryHandler

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL to send data to Make.com

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("No TOKEN or WEBHOOK_URL found in environment variables.")

# Initialize the bot application
application = Application.builder().token(TOKEN).build()

# Define states
CUSTOMER_NAME, ORDER_ITEM, PRICE, QUANTITY = range(4)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Let's create an order. Please enter the Customer Name:")
    context.user_data.clear()  # Clear previous data
    context.user_data['state'] = CUSTOMER_NAME
    return CUSTOMER_NAME

async def handle_customer_name(update: Update, context: CallbackContext):
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the Order Item:")
    context.user_data['state'] = ORDER_ITEM
    return ORDER_ITEM

async def handle_order_item(update: Update, context: CallbackContext):
    context.user_data['order_item'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the Price:")
    context.user_data['state'] = PRICE
    return PRICE

async def handle_price(update: Update, context: CallbackContext):
    try:
        price = float(update.message.text)
        if price <= 0:
            raise ValueError
        context.user_data['price'] = price
        await update.message.reply_text("Got it! Now, please enter the Quantity:")
        context.user_data['state'] = QUANTITY
        return QUANTITY
    except ValueError:
        await update.message.reply_text("Please enter a valid positive price.")
        return PRICE

async def handle_quantity(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()
    if user_input.lower() == 'cancel':
        await cancel(update, context)
        return ConversationHandler.END

    try:
        quantity = int(user_input)
        if quantity <= 0:
            raise ValueError
        price = float(context.user_data['price'])
        total_price = price * quantity
        order_summary = (f"Order Summary\n"
                         f"Customer Name: {context.user_data['customer_name']}\n"
                         f"Order Item: {context.user_data['order_item']}\n"
                         f"Price: {context.user_data['price']}\n"
                         f"Quantity: {quantity}\n"
                         f"Total Price: {total_price}")

        # Add a button to send receipt
        keyboard = [[InlineKeyboardButton("Send Receipt", callback_data='send_receipt')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(order_summary, reply_markup=reply_markup)
        context.user_data['state'] = None  # End the conversation after showing the summary
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid positive quantity.")
        return QUANTITY

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Order creation cancelled.")
    context.user_data.clear()  # Clear user data on cancel
    return ConversationHandler.END

async def restart(update: Update, context: CallbackContext):
    await update.message.reply_text("Restarting the order process. Please enter the Customer Name:")
    context.user_data.clear()  # Clear previous data when restarting
    return CUSTOMER_NAME

async def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'send_receipt':
        # Collect data
        user_data = context.user_data
        payload = {
            "customer_name": user_data.get('customer_name'),
            "order_item": user_data.get('order_item'),
            "price": user_data.get('price'),
            "quantity": user_data.get('quantity'),
            "total_price": float(user_data.get('price', 0)) * int(user_data.get('quantity', 0))
        }
        
        # Send data to Make.com
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.ok:
            # Handle success and send receipt
            receipt_url = response.json().get('receipt_url')
            if receipt_url:
                await query.message.reply_text("Your receipt is being processed. It will be sent to you shortly.")
                await context.bot.send_document(chat_id=update.effective_chat.id, document=receipt_url)
            else:
                await query.message.reply_text("There was an issue processing your receipt.")
        else:
            await query.message.reply_text("Failed to send data for receipt processing.")

# Define the ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_customer_name)],
        ORDER_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_item)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        CommandHandler('restart', restart)  # Add the /restart command as a fallback
    ],
    allow_reentry=True  # Allow users to re-enter the conversation at any point
)

# Add handlers and run the bot
application.add_handler(conv_handler)
application.add_handler(CommandHandler('cancel', cancel))
application.add_handler(CommandHandler('restart', restart))  # Add handler for /restart
application.add_handler(CallbackQueryHandler(button_click))  # Add handler for button clicks

if __name__ == '__main__':
    application.run_polling()
