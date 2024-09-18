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

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Let's create an order. Please enter the Customer Name:")
    context.user_data.clear()  # Clear previous data
    return CUSTOMER_NAME

async def customer_name(update: Update, context: CallbackContext):
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the order item:")
    return ORDER_ITEM

async def order_item(update: Update, context: CallbackContext):
    context.user_data['order_item'] = update.message.text
    await update.message.reply_text("Please enter the price for the item:")
    return PRICE

async def price(update: Update, context: CallbackContext):
    try:
        price = float(update.message.text)
        if price <= 0:
            raise ValueError("Price must be positive")
        context.user_data['price'] = price
        await update.message.reply_text("Almost done! Please enter the Quantity:")
        return QUANTITY
    except ValueError:
        await update.message.reply_text("Please enter a valid positive price.")
        return PRICE

async def quantity(update: Update, context: CallbackContext):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        total_price = context.user_data['price'] * quantity
        order_summary = (f"Order Summary\n"
                         f"Customer Name: {context.user_data['customer_name']}\n"
                         f"Order Item: {context.user_data['order_item']}\n"
                         f"Price: {context.user_data['price']}\n"
                         f"Quantity: {quantity}\n"
                         f"Total Price: {total_price}")
        await update.message.reply_text(order_summary)
        context.user_data.clear()  # Clear user data after the order is completed
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

# Define the ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
        ORDER_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_item)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity)],
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('restart', restart)],
    allow_reentry=True
)

# Add handlers and run the bot
application.add_handler(conv_handler)
application.add_handler(CommandHandler('cancel', cancel))
application.add_handler(CommandHandler('restart', restart))  # Add handler for /restart

if __name__ == '__main__':
    application.run_polling()
