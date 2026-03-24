import { useAuth } from '../context/AuthContext';

export default function RoleGuard({ allowedRoles = [], fallback = null, children }) {
  const { session } = useAuth();
  if (!session.loggedIn) return fallback;
  if (allowedRoles.length && !allowedRoles.includes(session.role)) {
    return fallback;
  }
  return children;
}
