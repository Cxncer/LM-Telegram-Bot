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
    context.user_data['state'] = CUSTOMER_NAME
    return CUSTOMER_NAME

async def handle_text(update: Update, context: CallbackContext, next_state, field_name):
    context.user_data[field_name] = update.message.text
    await update.message.reply_text(f"Got it! Now, please enter the order item:")
    context.user_data['state'] = next_state
    return next_state

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
        price = float(context.user_data['price'])
        total_price = price * quantity
        order_summary = (f"Order Summary\n"
                         f"-Customer Name: {context.user_data['customer_name']}\n"
                         f"-Order Item: {context.user_data['order_item']}\n"
                         f"-Price: {context.user_data['price']}\n"
                         f"-Quantity: {quantity}\n"
                         f"-Total Price: {total_price}")
        await update.message.reply_text(order_summary)
        context.user_data.clear()  # Clear user data after the order is completed
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid quantity.")
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
        CUSTOMER_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_text(u, c, ORDER_ITEM, 'customer_name'))
        ],
        ORDER_ITEM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_text(u, c, PRICE, 'order_item'))
        ],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity)],
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

if __name__ == '__main__':
    application.run_polling()
