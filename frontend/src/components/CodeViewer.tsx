import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { ReviewFinding } from '@/types/review'

interface CodeViewerProps {
  code: string
  language: string
  fileName: string
  findings?: ReviewFinding[]
  highlightLines?: number[]
}

export default function CodeViewer({ 
  code, 
  language, 
  findings = [],
  highlightLines = []
}: CodeViewerProps) {
  // Map findings to line numbers for highlighting
  const findingLines = new Map<number, string>()
  findings.forEach(f => {
    for (let i = f.start_line; i <= f.end_line; i++) {
      findingLines.set(i, f.severity)
    }
  })

  const getLanguage = (lang: string): string => {
    const ext = lang.split('.').pop()?.toLowerCase() || lang
    const langMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'tsx': 'tsx',
      'jsx': 'jsx',
      'c': 'c',
      'cpp': 'cpp',
      'rs': 'rust',
      'go': 'go',
    }
    return langMap[ext] || ext
  }

  const getHighlightColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'rgba(239, 68, 68, 0.15)'
      case 'high': return 'rgba(249, 115, 22, 0.15)'
      case 'medium': return 'rgba(234, 179, 8, 0.1)'
      case 'low': return 'rgba(59, 130, 246, 0.1)'
      default: return 'rgba(255, 255, 255, 0.05)'
    }
  }

  const getBorderColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return '#ef4444'
      case 'high': return '#f97316'
      case 'medium': return '#eab308'
      case 'low': return '#3b82f6'
      default: return 'rgba(255, 255, 255, 0.2)'
    }
  }

  return (
    <div className="rounded-xl overflow-hidden border border-white/5 bg-[#1e1e1e] shadow-2xl">
      <SyntaxHighlighter
        language={getLanguage(language)}
        style={oneDark}
        showLineNumbers
        wrapLines
        lineProps={(lineNumber) => {
          const style: React.CSSProperties = { display: 'block', width: '100%' }
          const severity = findingLines.get(lineNumber)
          
          if (severity) {
            style.backgroundColor = getHighlightColor(severity)
            style.borderLeft = `2px solid ${getBorderColor(severity)}`
            style.paddingLeft = '12px'
            style.marginLeft = '-14px'
          } else if (highlightLines.includes(lineNumber)) {
            style.backgroundColor = 'rgba(255, 255, 255, 0.05)'
            style.borderLeft = '2px solid rgba(255, 255, 255, 0.2)'
            style.paddingLeft = '12px'
            style.marginLeft = '-14px'
          }
          
          return { style }
        }}
        customStyle={{
          margin: 0,
          padding: '24px 12px',
          borderRadius: 0,
          fontSize: '13px',
          lineHeight: '1.6',
          background: 'transparent',
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
