import dbConnect from '../../../lib/dbConnect';
import User from '../../../models/User';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ message: 'Method not allowed.' });
  }

  try {
    await dbConnect();

    const { name, email, password, role, riskScore } = req.body || {};

    if (!name || !email || !password || !role) {
      return res.status(400).json({ message: 'Name, email, password, and role are required.' });
    }

    const normalizedEmail = String(email).toLowerCase().trim();
    const normalizedRole = String(role).toLowerCase().trim();
    const allowedRoles = ['admin', 'analyst', 'employee'];

    if (!allowedRoles.includes(normalizedRole)) {
      return res.status(400).json({ message: 'Role must be admin, analyst, or employee.' });
    }

    const existingUser = await User.findOne({ email: normalizedEmail });
    if (existingUser) {
      return res.status(409).json({ message: 'A user with this email already exists.' });
    }

    const parsedRiskScore = Number(riskScore);
    const normalizedRiskScore = Number.isFinite(parsedRiskScore) ? Math.max(0, Math.min(parsedRiskScore, 100)) : 0;

    const user = await User.create({
      name: String(name).trim(),
      email: normalizedEmail,
      password,
      role: normalizedRole,
      riskScore: normalizedRole === 'employee' ? normalizedRiskScore : 0,
    });

    return res.status(201).json({
      message: 'User registered successfully.',
      user: {
        id: String(user._id),
        name: user.name,
        email: user.email,
        role: user.role,
        riskScore: user.riskScore,
        createdAt: user.createdAt,
      },
    });
  } catch (error) {
    if (error.name === 'ValidationError') {
      return res.status(400).json({ message: error.message });
    }

    return res.status(error.statusCode || 500).json({
      message: error.message || 'Unable to register user.',
      error: error.message,
    });
  }
}
