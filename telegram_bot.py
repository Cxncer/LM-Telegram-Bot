import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# Initialize the bot application
application = Application.builder().token(TOKEN).build()

# Define states
CUSTOMER_NAME, ORDER_ITEM, PRICE, QUANTITY = range(4)

# Start the order conversation
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Please enter the Customer Name:")
    return CUSTOMER_NAME

# General handler for receiving text inputs
async def handle_input(update: Update, context: CallbackContext, next_state, field_name, prompt):
    context.user_data[field_name] = update.message.text
    await update.message.reply_text(prompt)
    return next_state

# Handle price and quantity
async def handle_quantity(update: Update, context: CallbackContext):
    try:
        quantity = int(update.message.text)
        total_price = float(context.user_data['price']) * quantity
        summary = (f"Order Summary:\n"
                   f"- Customer Name: {context.user_data['customer_name']}\n"
                   f"- Order Item: {context.user_data['order_item']}\n"
                   f"- Price: {context.user_data['price']}\n"
                   f"- Quantity: {quantity}\n"
                   f"- Total Price: {total_price}")
        await update.message.reply_text(summary)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid quantity.")
        return QUANTITY

# Cancel the conversation
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Order creation cancelled.")
    return ConversationHandler.END

# ConversationHandler setup
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_input(u, c, ORDER_ITEM, 'customer_name', "Enter the Order Item:"))],
        ORDER_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_input(u, c, PRICE, 'order_item', "Enter the Price:"))],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_input(u, c, QUANTITY, 'price', "Enter the Quantity:"))],
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# Add the conversation handler and start the bot
application.add_handler(conv_handler)

if __name__ == '__main__':
    application.run_polling()
