import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { ReviewFinding } from '@/types/review'
import { MessageSquare, Shield, Zap, Code2 } from 'lucide-react'
import SeverityBadge from './SeverityBadge'

interface CodeViewerProps {
  code: string
  language: string
  findings?: ReviewFinding[]
  highlightLines?: number[]
}

export default function CodeViewer({ 
  code, 
  language, 
  findings = [],
  highlightLines = []
}: CodeViewerProps) {
  const lines = code.split('\n')
  
  // Map findings to line numbers
  const findingsByLine = new Map<number, ReviewFinding[]>()
  findings.forEach(f => {
    const lineFindings = findingsByLine.get(f.start_line) || []
    lineFindings.push(f)
    findingsByLine.set(f.start_line, lineFindings)
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

  const getAgentIcon = (name: string) => {
    const lowerName = name.toLowerCase()
    if (lowerName.includes('security')) return <Shield className="h-3 w-3 text-red-500" />
    if (lowerName.includes('optimization') || lowerName.includes('performance')) return <Zap className="h-3 w-3 text-green-500" />
    return <Code2 className="h-3 w-3 text-yellow-500" />
  }

  const getAgentBg = (name: string) => {
    const lowerName = name.toLowerCase()
    if (lowerName.includes('security')) return 'bg-red-500/10 border-red-500/20'
    if (lowerName.includes('optimization') || lowerName.includes('performance')) return 'bg-green-500/10 border-green-500/20'
    return 'bg-yellow-500/10 border-yellow-500/20'
  }

  return (
    <div className="rounded-xl overflow-hidden border border-white/5 bg-[#1e1e1e] shadow-2xl font-mono text-[13px]">
      <div className="overflow-x-auto">
        <SyntaxHighlighter
          language={getLanguage(language)}
          style={oneDark}
          showLineNumbers={true}
          wrapLines={true}
          customStyle={{
            margin: 0,
            padding: '1rem 0',
            background: 'transparent',
          }}
          lineNumberStyle={{
            minWidth: '3.5rem',
            paddingRight: '1.5rem',
            textAlign: 'right',
            color: '#4b5563',
            userSelect: 'none',
            borderRight: '1px solid rgba(255,255,255,0.05)',
            marginRight: '1rem',
          }}
          renderer={({ rows, stylesheet, useInlineStyles }) => {
            return rows.map((row, idx) => {
              const lineNumber = idx + 1
              const lineFindings = findingsByLine.get(lineNumber)
              const isHighlighted = highlightLines.includes(lineNumber)
              
              const rowNode = (
                <div 
                  key={`line-${idx}`}
                  style={{ 
                    ...row.properties.style,
                    backgroundColor: isHighlighted ? 'rgba(255,255,255,0.05)' : 'transparent',
                    display: 'flex',
                  }}
                >
                  <span style={{ 
                    minWidth: '3.5rem', 
                    paddingRight: '1.5rem', 
                    textAlign: 'right', 
                    color: '#4b5563', 
                    borderRight: '1px solid rgba(255,255,255,0.05)',
                    marginRight: '1rem',
                    flexShrink: 0
                  }}>
                    {lineNumber}
                  </span>
                  <span style={{ flexGrow: 1 }}>
                    {row.children.map((token, key) => (
                      <span key={key} style={token.properties?.style}>
                        {token.children?.[0]?.value || ''}
                      </span>
                    ))}
                  </span>
                </div>
              )

              if (!lineFindings) return rowNode

              return (
                <React.Fragment key={`group-${idx}`}>
                  {rowNode}
                  {lineFindings.map(finding => (
                    <div key={finding.id} className="flex bg-[#1e1e1e]">
                      <div className="min-width-[3.5rem] w-[3.5rem] border-r border-white/5 mr-[1rem] flex-shrink-0"></div>
                      <div className="px-4 py-3 flex-grow">
                        <div className={`rounded-lg border p-4 my-2 max-w-3xl ${getAgentBg(finding.agent_name)} shadow-lg`}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              {getAgentIcon(finding.agent_name)}
                              <span className="text-[10px] font-bold uppercase tracking-widest opacity-80">
                                {finding.agent_name}
                              </span>
                            </div>
                            <SeverityBadge severity={finding.severity} showLabel={true} className="scale-75 origin-right" />
                          </div>
                          <h6 className="font-bold text-white mb-1">{finding.title}</h6>
                          <p className="text-gray-300 text-xs leading-relaxed mb-3">
                            {finding.description}
                          </p>
                          {finding.suggestion && (
                            <div className="text-[11px] bg-black/30 p-2 rounded border border-white/5 text-gray-400 italic">
                              <span className="font-bold text-gray-300 not-italic mr-1">Suggestion:</span>
                              {finding.suggestion}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </React.Fragment>
              )
            })
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}
