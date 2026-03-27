const express = require("express");
const router = express.Router();
const { analyze } = require("../controllers/analyticsController");
const { authenticateUser, authorizeRoles } = require("../middleware/authMiddleware");

router.post("/analyze", authenticateUser, authorizeRoles("admin", "analyst"), analyze);

module.exports = router;
