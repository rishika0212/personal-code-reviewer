import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion'
import { Badge } from './ui/badge'
import SeverityBadge from './SeverityBadge'
import type { ReviewFinding } from '@/types/review'

interface AgentCommentsProps {
  findings: ReviewFinding[]
  onFindingClick?: (finding: ReviewFinding) => void
}

export default function AgentComments({ findings, onFindingClick }: AgentCommentsProps) {
  // Group findings by category
  const groupedFindings = findings.reduce((acc, finding) => {
    const category = finding.category || 'General'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(finding)
    return acc
  }, {} as Record<string, ReviewFinding[]>)

  if (findings.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No issues found. Your code looks good! 🎉
      </div>
    )
  }

  return (
    <Accordion type="multiple" className="w-full">
      {Object.entries(groupedFindings).map(([category, categoryFindings]) => (
        <AccordionItem key={category} value={category}>
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <span className="font-medium">{category}</span>
              <Badge variant="outline">{categoryFindings.length}</Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4">
              {categoryFindings.map((finding) => (
                <div
                  key={finding.id}
                  className="border rounded-lg p-4 cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => onFindingClick?.(finding)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <SeverityBadge severity={finding.severity} />
                        <span className="font-medium">{finding.title}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {finding.description}
                      </p>
                      <div className="text-xs text-muted-foreground">
                        <span className="font-mono">{finding.file_path}</span>
                        <span className="mx-2">•</span>
                        <span>Lines {finding.start_line}-{finding.end_line}</span>
                      </div>
                    </div>
                  </div>
                  
                  {finding.suggestion && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-sm">
                        <span className="font-medium">Suggestion: </span>
                        {finding.suggestion}
                      </p>
                    </div>
                  )}
                  
                  {finding.code_snippet && (
                    <div className="mt-3 pt-3 border-t">
                      <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                        <code>{finding.code_snippet}</code>
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
