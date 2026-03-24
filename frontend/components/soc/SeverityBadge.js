import StatusBadge from './StatusBadge';

export default function SeverityBadge({ level = 'medium', children }) {
  return <StatusBadge tone={level}>{children || level}</StatusBadge>;
}
