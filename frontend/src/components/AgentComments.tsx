import SeverityBadge from './SeverityBadge'
import type { ReviewFinding } from '@/types/review'
import { MessageSquare, Lightbulb, Code } from 'lucide-react'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion'

interface AgentCommentsProps {
  findings: ReviewFinding[]
  onFindingClick?: (finding: ReviewFinding) => void
  selectedFindingIds?: string[]
  onToggleFinding?: (findingId: string) => void
}

export default function AgentComments({ 
  findings, 
  onFindingClick,
  selectedFindingIds = [],
  onToggleFinding
}: AgentCommentsProps) {
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
      <div className="text-center py-24 bg-white rounded-xl border border-dashed border-border/60">
        <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center text-green-600 mx-auto mb-6">
          <MessageSquare className="h-8 w-8" />
        </div>
        <h3 className="text-xl font-serif mb-2">Pristine Codebase</h3>
        <p className="text-muted-foreground font-sans max-w-xs mx-auto">
          Our analysis has concluded with no findings. The architectural integrity of this code is exceptional.
        </p>
      </div>
    )
  }

  return (
    <Accordion type="multiple" className="w-full space-y-4">
      {Object.entries(groupedFindings).map(([category, categoryFindings]) => (
        <AccordionItem key={category} value={category} className="border-none">
          <AccordionTrigger className="hover:no-underline py-2">
            <div className="flex items-center gap-3 w-full pr-4">
              <h4 className="text-sm font-bold uppercase tracking-widest text-accent/80">{category}</h4>
              <div className="h-[1px] flex-grow bg-border/40"></div>
              <span className="text-xs font-medium text-muted-foreground">{categoryFindings.length} findings</span>
            </div>
          </AccordionTrigger>
          
          <AccordionContent className="pt-4 pb-2">
            <div className="grid gap-4">
              {categoryFindings.map((finding) => {
                const getAgentColor = (name: string) => {
                  const lowerName = name.toLowerCase()
                  if (lowerName.includes('security')) return 'border-l-red-500'
                  if (lowerName.includes('optimization') || lowerName.includes('performance')) return 'border-l-green-500'
                  return 'border-l-yellow-500' // Default for code quality
                }

                return (
                  <div
                    key={finding.id}
                    className={`group relative bg-white border border-border/50 border-l-4 ${getAgentColor(finding.agent_name)} rounded-xl overflow-hidden shadow-sm hover:shadow-md hover:border-accent/20 transition-all duration-300 cursor-pointer ${selectedFindingIds.includes(finding.id) ? 'ring-2 ring-accent/30 bg-accent/5' : ''}`}
                    onClick={() => onFindingClick?.(finding)}
                  >
                  <div className="p-5 sm:p-6">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex items-center gap-3 mt-1" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedFindingIds.includes(finding.id)}
                          onChange={() => onToggleFinding?.(finding.id)}
                          className="w-4 h-4 rounded border-gray-300 text-accent focus:ring-accent cursor-pointer"
                        />
                      </div>
                      <div className="flex-grow space-y-1.5">
                        <div className="flex items-center gap-3">
                          <SeverityBadge severity={finding.severity} />
                          <h5 className="font-serif font-bold text-lg leading-tight group-hover:text-accent transition-colors">
                            {finding.title}
                          </h5>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-muted-foreground font-mono bg-secondary/30 px-2 py-0.5 rounded w-fit">
                          <Code className="h-3 w-3" />
                          <span>{finding.file_path.split('/').pop()}</span>
                          <span>:</span>
                          <span>{finding.start_line}</span>
                        </div>
                      </div>
                    </div>

                    <p className="text-muted-foreground leading-relaxed text-sm mb-5 font-sans">
                      {finding.description}
                    </p>
                    
                    {(finding.suggestion || finding.code_snippet) && (
                      <div className="space-y-4 pt-4 border-t border-border/40">
                        {finding.suggestion && (
                          <div className="flex gap-3 bg-accent/5 p-4 rounded-lg border border-accent/10">
                            <Lightbulb className="h-5 w-5 text-accent flex-shrink-0" />
                            <div className="space-y-1">
                              <p className="text-[10px] font-bold uppercase tracking-widest text-accent">Recommendation</p>
                              <p className="text-sm text-foreground/80 leading-relaxed font-sans italic">
                                "{finding.suggestion}"
                              </p>
                            </div>
                          </div>
                        )}
                        
                        {finding.code_snippet && (
                          <div className="space-y-1.5">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground px-1">Implementation Context</p>
                            <pre className="text-xs bg-[#1e1e1e] text-gray-300 p-4 rounded-lg overflow-x-auto font-mono leading-relaxed border border-white/5 shadow-inner">
                              <code>{finding.code_snippet}</code>
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )})}
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
