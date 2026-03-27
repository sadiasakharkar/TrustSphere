import jwt from 'jsonwebtoken';
import dbConnect from './dbConnect';
import User from '../models/User';

export function generateToken(user) {
  const jwtSecret = process.env.JWT_SECRET;

  if (!jwtSecret) {
    throw new Error('JWT authentication is not configured. Set JWT_SECRET in frontend/.env.local.');
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
  const jwtSecret = process.env.JWT_SECRET;

  if (!jwtSecret) {
    const error = new Error('JWT authentication is not configured. Set JWT_SECRET in frontend/.env.local.');
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
    createdAt: user.createdAt,
  };
}
