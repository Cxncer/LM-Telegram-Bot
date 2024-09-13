// server.js

const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Simple route to handle the homepage
app.get('/', (req, res) => {
  res.send('Hello from Glitch!');
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
