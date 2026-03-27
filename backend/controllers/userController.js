const User = require("../models/User");

exports.listUsers = async (req, res) => {
  try {
    const users = await User.find().select("-password").sort({ createdAt: -1 });
    return res.status(200).json({
      message: "Users fetched successfully.",
      users,
    });
  } catch (error) {
    return res.status(500).json({ message: "Unable to fetch users.", error: error.message });
  }
};

exports.createUser = async (req, res) => {
  try {
    const { name, email, password, role, riskScore } = req.body;

    if (!name || !email || !password || !role) {
      return res.status(400).json({ message: "Name, email, password, and role are required." });
    }

    const normalizedEmail = String(email).toLowerCase().trim();
    const normalizedRole = String(role).toLowerCase().trim();
    const allowedRoles = ["admin", "analyst", "employee"];

    if (!allowedRoles.includes(normalizedRole)) {
      return res.status(400).json({ message: "Role must be admin, analyst, or employee." });
    }

    const existingUser = await User.findOne({ email: normalizedEmail });
    if (existingUser) {
      return res.status(409).json({ message: "A user with this email already exists." });
    }

    const parsedRiskScore = Number(riskScore);
    const normalizedRiskScore = Number.isFinite(parsedRiskScore) ? Math.max(0, Math.min(parsedRiskScore, 100)) : 0;

    const user = await User.create({
      name: String(name).trim(),
      email: normalizedEmail,
      password,
      role: normalizedRole,
      riskScore: normalizedRole === "employee" ? normalizedRiskScore : 0,
    });

    return res.status(201).json({
      message: "User created successfully.",
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        riskScore: user.riskScore,
        createdAt: user.createdAt,
      },
    });
  } catch (error) {
    if (error.name === "ValidationError") {
      return res.status(400).json({ message: error.message });
    }
    return res.status(500).json({ message: "Unable to create user.", error: error.message });
  }
};

exports.updateUserRole = async (req, res) => {
  try {
    const { id } = req.params;
    const { role, riskScore } = req.body;
    const normalizedRole = String(role || "").toLowerCase().trim();
    const allowedRoles = ["admin", "analyst", "employee"];

    if (!allowedRoles.includes(normalizedRole)) {
      return res.status(400).json({ message: "Role must be admin, analyst, or employee." });
    }

    const user = await User.findById(id);
    if (!user) {
      return res.status(404).json({ message: "User not found." });
    }

    user.role = normalizedRole;
    if (normalizedRole === "employee") {
      const parsedRiskScore = Number(riskScore);
      user.riskScore = Number.isFinite(parsedRiskScore) ? Math.max(0, Math.min(parsedRiskScore, 100)) : user.riskScore;
    } else {
      user.riskScore = 0;
    }

    await user.save();

    return res.status(200).json({
      message: "User role updated successfully.",
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        riskScore: user.riskScore,
        createdAt: user.createdAt,
        lastLogin: user.lastLogin,
      },
    });
  } catch (error) {
    return res.status(500).json({ message: "Unable to update user role.", error: error.message });
  }
};

exports.deleteUser = async (req, res) => {
  try {
    const { id } = req.params;

    const user = await User.findByIdAndDelete(id);
    if (!user) {
      return res.status(404).json({ message: "User not found." });
    }

    return res.status(200).json({
      message: "User deleted successfully.",
      user: {
        id: user._id,
        email: user.email,
        role: user.role,
      },
    });
  } catch (error) {
    return res.status(500).json({ message: "Unable to delete user.", error: error.message });
  }
};
