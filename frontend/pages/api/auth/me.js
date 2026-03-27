import { getUserFromRequest } from '../../../lib/auth';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ message: 'Method not allowed.' });
  }

  try {
    const user = await getUserFromRequest(req);
    return res.status(200).json({
      message: 'User verified successfully.',
      user,
    });
  } catch (error) {
    return res.status(error.statusCode || 401).json({
      message: error.message || 'Unauthorized access.',
    });
  }
}
