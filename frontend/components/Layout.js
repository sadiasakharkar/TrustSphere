import AppShell from './soc/AppShell';

export default function Layout({ children, insightSummary = null }) {
  return <AppShell insightSummary={insightSummary}>{children}</AppShell>;
}
