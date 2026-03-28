export function getDefaultRouteForRole(role) {
  const normalized = String(role || 'employee').toLowerCase();

  if (normalized === 'admin') return '/dashboard/admin';
  if (normalized === 'analyst') return '/dashboard/analyst';
  return '/dashboard/employee';
}
