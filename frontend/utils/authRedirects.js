export function getDefaultRouteForRole(role) {
  const normalized = String(role || 'employee').toLowerCase();

  if (normalized === 'admin') return '/admin';
  return '/overview';
}
