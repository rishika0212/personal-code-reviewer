import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
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
  fileName, 
  findings = [],
  highlightLines = []
}: CodeViewerProps) {
  // Map findings to line numbers for highlighting
  const findingLines = new Set(
    findings.flatMap(f => {
      const lines = []
      for (let i = f.start_line; i <= f.end_line; i++) {
        lines.push(i)
      }
      return lines
    })
  )

  // Combine with explicit highlight lines
  const allHighlightLines = new Set([...findingLines, ...highlightLines])

  const getLanguage = (lang: string): string => {
    const langMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'tsx': 'tsx',
      'jsx': 'jsx',
    }
    return langMap[lang] || lang
  }

  return (
    <div className="rounded-lg overflow-hidden border">
      <div className="bg-muted px-4 py-2 border-b">
        <span className="text-sm font-mono text-muted-foreground">{fileName}</span>
      </div>
      <SyntaxHighlighter
        language={getLanguage(language)}
        style={vscDarkPlus}
        showLineNumbers
        wrapLines
        lineProps={(lineNumber) => {
          const style: React.CSSProperties = { display: 'block' }
          if (allHighlightLines.has(lineNumber)) {
            style.backgroundColor = 'rgba(255, 220, 0, 0.2)'
            style.borderLeft = '3px solid #ffd700'
            style.paddingLeft = '8px'
            style.marginLeft = '-11px'
          }
          return { style }
        }}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: '14px',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
