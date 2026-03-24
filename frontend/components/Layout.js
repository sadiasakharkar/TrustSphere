import AppShell from './soc/AppShell';

export default function Layout({ children, insightSummary }) {
  return <AppShell insightSummary={insightSummary}>{children}</AppShell>;
}
