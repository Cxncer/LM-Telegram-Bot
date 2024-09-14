require('dotenv').config();
const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.TOKEN);

// Check if the TOKEN is loaded properly
if (!process.env.TOKEN) {
    console.error("Error: Bot Token is missing!");
    process.exit(1);
}

bot.start((ctx) => ctx.reply('Welcome to the bot!'));

// Set webhook or polling based on your setup
bot.launch();

console.log('Bot is up and running...');
