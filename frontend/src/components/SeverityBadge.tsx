import { Badge } from './ui/badge'

interface SeverityBadgeProps {
  severity: string
  showLabel?: boolean
}

export default function SeverityBadge({ severity, showLabel = true }: SeverityBadgeProps) {
  const getVariant = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'critical' as const
      case 'high':
        return 'high' as const
      case 'medium':
        return 'medium' as const
      case 'low':
        return 'low' as const
      case 'info':
        return 'info' as const
      default:
        return 'outline' as const
    }
  }

  const getIcon = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return '🔴'
      case 'high':
        return '🟠'
      case 'medium':
        return '🟡'
      case 'low':
        return '🔵'
      case 'info':
        return 'ℹ️'
      default:
        return '⚪'
    }
  }

  return (
    <Badge variant={getVariant(severity)}>
      {getIcon(severity)} {showLabel && severity.toUpperCase()}
    </Badge>
  )
}
