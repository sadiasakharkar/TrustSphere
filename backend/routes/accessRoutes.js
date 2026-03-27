const express = require("express");
const {
  adminAccess,
  analystAccess,
  employeeAccess,
} = require("../controllers/accessController");

const router = express.Router();

router.get("/admin", adminAccess);
router.get("/analyst", analystAccess);
router.get("/employee", employeeAccess);

module.exports = router;
