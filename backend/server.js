const express = require("express");
const app = express();

app.use(express.json());

const analyticsRoutes = require("./routes/analyticsRoutes");

app.use("/api/analytics", analyticsRoutes);

app.listen(5000, () => {
    console.log("Backend running on port 5000");
});