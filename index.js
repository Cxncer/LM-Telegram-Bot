const express = require('express');
const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.BOT_TOKEN);

const app = express();

// Telegraf uses Express middleware for webhook integration
app.use(bot.webhookCallback('/bot'));

// Set webhook for the bot on the correct URL
bot.telegram.setWebhook(`lmtelegrambot.vercel.app`);

// Listen to Vercel's port
app.listen(3000, () => {
  console.log('Bot is running...');
});
