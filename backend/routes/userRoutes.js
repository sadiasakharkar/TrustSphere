const express = require("express");
const {
  listUsers,
  createUser,
  updateUserRole,
  deleteUser,
} = require("../controllers/userController");
const { authenticateUser, authorizeRoles } = require("../middleware/authMiddleware");

const router = express.Router();

router.use(authenticateUser, authorizeRoles("admin"));

router.get("/", listUsers);
router.post("/", createUser);
router.patch("/:id/role", updateUserRole);
router.delete("/:id", deleteUser);

module.exports = router;
