import dbConnect from '../../../lib/dbConnect';
import { generateToken } from '../../../lib/auth';
import User from '../../../models/User';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ message: 'Method not allowed.' });
  }

  try {
    await dbConnect();

    const { email, password } = req.body || {};

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required.' });
    }

    const normalizedEmail = String(email).toLowerCase().trim();
    const user = await User.findOne({ email: normalizedEmail });

    if (!user) {
      return res.status(404).json({ message: 'User not found. Please register yourself first.' });
    }

    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    user.lastLogin = new Date();
    await user.save();

    const token = generateToken(user);

    return res.status(200).json({
      message: 'Login successful.',
      token,
      user: {
        id: String(user._id),
        name: user.name,
        email: user.email,
        role: user.role,
        riskScore: user.riskScore || 0,
        lastLogin: user.lastLogin,
      },
    });
  } catch (error) {
    return res.status(error.statusCode || 500).json({
      message: error.message || 'Unable to login.',
      error: error.message,
    });
  }
}
