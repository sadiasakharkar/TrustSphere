require("dotenv").config();

const express = require("express");
const analyticsRoutes = require("./routes/analyticsRoutes");
const accessRoutes = require("./routes/accessRoutes");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(express.json());

app.get("/", async (req, res) => {
  return res.status(200).json({
    message: "TrustSphere backend is running.",
  });
});

app.use("/api", accessRoutes);
app.use("/api/analytics", analyticsRoutes);

app.use((req, res) => {
  return res.status(404).json({ message: "Route not found." });
});

app.use((error, req, res, next) => {
  console.error(error);
  return res.status(500).json({
    message: "Internal server error.",
    error: error.message,
  });
});

app.listen(PORT, () => {
  console.log(`Backend running on port ${PORT}`);
});
