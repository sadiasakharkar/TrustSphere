export function getDefaultRouteForRole(role) {
  const normalized = String(role || 'analyst').toLowerCase();

  if (normalized === 'admin') return '/administration';
  if (normalized === 'employee') return '/monitoring';
  return '/overview';
}
