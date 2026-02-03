import { cn } from "@/lib/utils"

interface SeverityBadgeProps {
  severity: string
  showLabel?: boolean
  className?: string
}

export default function SeverityBadge({ severity, showLabel = true, className }: SeverityBadgeProps) {
  const getStyles = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-red-50/50 text-red-900 border-red-200/50 shadow-[0_0_8px_rgba(239,68,68,0.1)]'
      case 'high':
        return 'bg-orange-50/50 text-orange-900 border-orange-200/50 shadow-[0_0_8px_rgba(249,115,22,0.1)]'
      case 'medium':
        return 'bg-amber-50/50 text-amber-900 border-amber-200/50'
      case 'low':
        return 'bg-emerald-50/50 text-emerald-900 border-emerald-200/50'
      case 'info':
        return 'bg-slate-50/50 text-slate-900 border-slate-200/50'
      default:
        return 'bg-slate-50/50 text-slate-900 border-slate-200/50'
    }
  }

  const getDotColor = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical': return 'bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.5)]'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-amber-500'
      case 'low': return 'bg-emerald-500'
      case 'info': return 'bg-slate-400'
      default: return 'bg-slate-400'
    }
  }

  return (
    <div className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[9px] font-semibold tracking-widest uppercase backdrop-blur-[2px]",
      getStyles(severity),
      className
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full", getDotColor(severity))} />
      {showLabel && severity}
    </div>
  )
}
