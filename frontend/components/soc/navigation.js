export const socNavigation = [
  { href: '/overview', label: 'Overview', icon: 'dashboard', allowedRoles: ['analyst', 'admin'] },
  { href: '/monitoring', label: 'Monitoring', icon: 'monitoring', allowedRoles: ['analyst', 'admin'] },
  { href: '/triage', label: 'Triage', icon: 'assignment', allowedRoles: ['analyst', 'admin'] },
  { href: '/investigations', label: 'Investigations', icon: 'search_insights', allowedRoles: ['analyst', 'admin'] },
  { href: '/threat-graph', label: 'Attack Graph', icon: 'hub', allowedRoles: ['analyst', 'admin'] },
  { href: '/response', label: 'Response', icon: 'playlist_add_check', allowedRoles: ['analyst', 'admin'] },
  { href: '/reports', label: 'Reports', icon: 'description', allowedRoles: ['analyst', 'admin'] },
  { href: '/analytics', label: 'Analytics', icon: 'analytics', allowedRoles: ['analyst', 'admin'] },
  { href: '/detections', label: 'Detections', icon: 'shield_lock', allowedRoles: ['admin'] },
  { href: '/administration', label: 'Administration', icon: 'admin_panel_settings', allowedRoles: ['admin'] },
  { href: '/settings', label: 'Settings', icon: 'settings', allowedRoles: ['admin'] }
];
