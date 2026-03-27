import jwt from 'jsonwebtoken';
import dbConnect from './dbConnect';
import User from '../models/User';

function getJwtSecret() {
  return process.env.JWT_SECRET || process.env.AUTH_JWT_SECRET || '';
}

export function generateToken(user) {
  const jwtSecret = getJwtSecret();

  if (!jwtSecret) {
    const error = new Error('JWT secret is not configured. Set JWT_SECRET.');
    error.statusCode = 500;
    throw error;
  }

  return jwt.sign(
    {
      id: String(user._id),
      email: user.email,
      role: user.role,
    },
    jwtSecret,
    { expiresIn: '1d' }
  );
}

export async function getUserFromRequest(req) {
  const jwtSecret = getJwtSecret();

  if (!jwtSecret) {
    const error = new Error('JWT secret is not configured. Set JWT_SECRET.');
    error.statusCode = 500;
    throw error;
  }

  const authHeader = req.headers.authorization || '';

  if (!authHeader.startsWith('Bearer ')) {
    const error = new Error('Access denied. Token is missing.');
    error.statusCode = 401;
    throw error;
  }

  const token = authHeader.split(' ')[1];
  const decoded = jwt.verify(token, jwtSecret);

  await dbConnect();
  const user = await User.findById(decoded.id).select('-password');

  if (!user) {
    const error = new Error('Invalid token. User not found.');
    error.statusCode = 401;
    throw error;
  }

  return {
    id: String(user._id),
    name: user.name,
    email: user.email,
    role: user.role,
    riskScore: user.riskScore || 0,
    lastLogin: user.lastLogin || null,
    createdAt: user.createdAt,
  };
}
