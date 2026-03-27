import { getUserFromRequest } from '../../lib/auth';

export default async function handler(req, res) {
  try {
    const user = await getUserFromRequest(req);

    if (!['admin', 'analyst'].includes(user.role)) {
      return res.status(403).json({ message: 'Forbidden. Analyst or admin access only.' });
    }

    return res.status(200).json({
      message: 'Analyst access granted.',
      user,
    });
  } catch (error) {
    return res.status(error.statusCode || 401).json({
      message: error.message || 'Unauthorized access.',
    });
  }
}
