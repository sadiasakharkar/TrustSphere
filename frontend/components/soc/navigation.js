export const socNavigation = {
  employee: [
    { href: '/overview', label: 'Overview', icon: 'dashboard' },
    { href: '/email', label: 'Request Analysis', icon: 'mail' },
    { href: '/postman', label: 'Postman', icon: 'send' },
    { href: '/monitoring', label: 'My Alerts', icon: 'monitoring' },
  ],
  analyst: [
    { href: '/overview', label: 'Overview', icon: 'dashboard' },
    { href: '/email', label: 'Email Analyzer', icon: 'mail' },
    { href: '/incidents', label: 'Incidents', icon: 'assignment' },
    { href: '/monitoring', label: 'Alerts', icon: 'monitoring' },
    { href: '/investigations', label: 'Investigations', icon: 'search_insights' },
    { href: '/threat-graph', label: 'Attack Graph', icon: 'hub' },
    { href: '/playbooks', label: 'Playbooks', icon: 'playlist_add_check' },
    { href: '/analytics', label: 'AI Insights', icon: 'analytics' },
    { href: '/postman', label: 'Postman', icon: 'send' },
  ],
  admin: [
    { href: '/overview', label: 'Overview', icon: 'dashboard' },
    { href: '/email', label: 'Email Analyzer', icon: 'mail' },
    { href: '/settings', label: 'System Health', icon: 'monitor_heart' },
    { href: '/detections', label: 'Model Monitoring', icon: 'shield_lock' },
    { href: '/administration', label: 'User Management', icon: 'group' },
    { href: '/monitoring', label: 'Data Sources', icon: 'lan' },
    { href: '/reports', label: 'Compliance Logs', icon: 'fact_check' },
    { href: '/postman', label: 'Postman', icon: 'send' },
    { href: '/settings', label: 'Configuration', icon: 'settings' },
  ],
};

export function getNavigationForRole(role) {
  return socNavigation[role] || socNavigation.analyst;
}
