import { getUserFromRequest } from '../../lib/auth';

export default async function handler(req, res) {
  try {
    const user = await getUserFromRequest(req);

    if (user.role !== 'admin') {
      return res.status(403).json({ message: 'Forbidden. Admin access only.' });
    }

    return res.status(200).json({
      message: 'Admin access granted.',
      user,
    });
  } catch (error) {
    return res.status(error.statusCode || 401).json({
      message: error.message || 'Unauthorized access.',
    });
  }
}
