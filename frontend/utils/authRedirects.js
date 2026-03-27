export function getDefaultRouteForRole(role) {
  const normalizedRole = String(role || 'analyst').toLowerCase();

  if (normalizedRole === 'admin') return '/administration';
  if (normalizedRole === 'employee') return '/monitoring';
  return '/overview';
}
