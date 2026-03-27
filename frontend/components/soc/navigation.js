export const socNavigation = {
  analyst: [
    { href: '/overview', label: 'Dashboard', icon: 'dashboard' },
    { href: '/monitoring', label: 'Alerts', icon: 'warning' },
    { href: '/analytics', label: 'AI Analysis', icon: 'psychology' },
    { href: '/incidents', label: 'Incidents', icon: 'assignment' },
    { href: '/email', label: 'Data Input', icon: 'upload_file' },
  ],
  admin: [
    { href: '/overview', label: 'Dashboard', icon: 'dashboard' },
    { href: '/monitoring', label: 'Alerts', icon: 'warning' },
    { href: '/analytics', label: 'AI Analysis', icon: 'psychology' },
    { href: '/incidents', label: 'Incidents', icon: 'assignment' },
    { href: '/email', label: 'Data Input', icon: 'upload_file' },
    { href: '/settings', label: 'Configuration', icon: 'settings' },
  ],
};

export function getNavigationForRole(role) {
  return socNavigation[role] || socNavigation.analyst;
}
