import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variable
TOKEN = os.getenv('TOKEN')

# Define states for the conversation
CUSTOMER_NAME, ORDER_ITEM, PRICE, QUANTITY, TOTAL_PRICE = range(5)

async def start(update: Update, context):
    await update.message.reply_text("Welcome! Let's create an order. Please enter the Customer Name:")
    return CUSTOMER_NAME

async def customer_name(update: Update, context):
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the Order Item:")
    return ORDER_ITEM

async def order_item(update: Update, context):
    context.user_data['order_item'] = update.message.text
    await update.message.reply_text("Great! Please enter the Price:")
    return PRICE

async def price(update: Update, context):
    context.user_data['price'] = update.message.text
    await update.message.reply_text("Almost done! Please enter the Quantity:")
    return QUANTITY

async def quantity(update: Update, context):
    context.user_data['quantity'] = update.message.text
    
    # Calculate the total price
    price = float(context.user_data['price'])
    quantity = int(context.user_data['quantity'])
    context.user_data['total_price'] = price * quantity
    
    await update.message.reply_text(f"Thank you! The Total Price is {context.user_data['total_price']}.")
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("Order creation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
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
    application.run_polling()

if __name__ == '__main__':
    main()
