const express = require("express");
const {
  adminAccess,
  analystAccess,
  employeeAccess,
} = require("../controllers/accessController");
const { protect, authorize } = require("../middleware/authMiddleware");

const router = express.Router();

router.get("/admin", protect, authorize("admin"), adminAccess);
router.get("/analyst", protect, authorize("admin", "analyst"), analystAccess);
router.get("/employee", protect, authorize("admin", "analyst", "employee"), employeeAccess);

module.exports = router;
