import { getUserFromRequest } from '../../lib/auth';

export default async function handler(req, res) {
  try {
    const user = await getUserFromRequest(req);

    if (!['admin', 'analyst', 'employee'].includes(user.role)) {
      return res.status(403).json({ message: 'Forbidden. Invalid role.' });
    }

    return res.status(200).json({
      message: 'Employee access granted.',
      user,
    });
  } catch (error) {
    return res.status(error.statusCode || 401).json({
      message: error.message || 'Unauthorized access.',
    });
  }
}
