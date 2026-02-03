import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { ArrowLeft, Loader2, AlertCircle, CheckCircle2, LayoutGrid, FileCode, ScrollText, Shield, Code2, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import FileTree from '@/components/FileTree'
import CodeViewer from '@/components/CodeViewer'
import AgentComments from '@/components/AgentComments'
import { useReviewStatus } from '@/hooks/useReviewStatus'
import { getReviewResults } from '@/api/reviewApi'
import type { ReviewResponse, ReviewFinding } from '@/types/review'

export default function Review() {
  const { reviewId } = useParams<{ reviewId: string }>()
  const { status, progress, error: statusError } = useReviewStatus(reviewId!)
  const [results, setResults] = useState<ReviewResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>('')

  const fetchResults = useCallback(async () => {
    if (!reviewId) return
    try {
      const data = await getReviewResults(reviewId)
      setResults(data)
    } catch (err) {
      console.error('Failed to fetch results:', err)
    }
  }, [reviewId])

  useEffect(() => {
    let isMounted = true
    if (status === 'completed' && reviewId) {
      const loadResults = async () => {
        if (isMounted) {
          await fetchResults()
        }
      }
      loadResults()
    }
    return () => { isMounted = false }
  }, [status, reviewId, fetchResults])

  const handleFileSelect = (path: string) => {
    setSelectedFile(path)
    // In a real app, fetch file content from API
    setFileContent('// File content would be loaded here\n\nfunction example() {\n  console.log("This is a placeholder for file content");\n}')
  }

  const handleFindingClick = (finding: ReviewFinding) => {
    setSelectedFile(finding.file_path)
  }

  const getFileFindings = (filePath: string): ReviewFinding[] => {
    if (!results) return []
    return results.findings.filter(f => f.file_path === filePath)
  }

  // Show loading state
  if (status === 'pending' || status === 'processing') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full text-center space-y-8 animate-in fade-in duration-1000">
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-accent/20 animate-ping duration-[2000ms]"></div>
              <div className="relative bg-card p-6 rounded-full shadow-xl border border-border">
                <Loader2 className="h-12 w-12 animate-spin text-accent" />
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <h1 className="text-3xl font-serif tracking-tight">Analyzing Codebase</h1>
            <p className="text-muted-foreground font-sans max-w-sm mx-auto">
              Our autonomous agents are meticulously evaluating your code for architectural integrity and security.
            </p>
          </div>
          <div className="space-y-3">
            <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-accent transition-all duration-700 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between text-xs font-medium tracking-widest uppercase text-muted-foreground">
              <span>Analysis in progress</span>
              <span>{progress}%</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Show error state
  if (status === 'failed' || statusError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <Card className="max-w-md w-full border-destructive/20 shadow-2xl">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center text-destructive mb-4">
              <AlertCircle className="h-8 w-8" />
            </div>
            <CardTitle className="text-2xl font-serif">Review Encountered an Error</CardTitle>
            <CardDescription className="text-base pt-2">
              {statusError || 'An unexpected issue occurred during the analysis phase.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center pt-4">
            <Link to="/">
              <Button variant="outline" className="px-8">
                Return to Safety
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Subtle decorative background */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/3 blur-[100px] rounded-full pointer-events-none -mr-48 -mt-48 animate-float"></div>
      <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-accent/2 blur-[80px] rounded-full pointer-events-none -ml-24 -mb-24 animate-float" style={{ animationDelay: '-3s' }}></div>
      
      {/* Refined Header */}
      <header className="border-b border-border/60 bg-transparent backdrop-blur-md sticky top-0 z-50 relative">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/">
              <Button variant="ghost" size="icon" className="rounded-full hover:bg-secondary">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div className="h-8 w-[1px] bg-border/60 hidden sm:block"></div>
            <div>
              <h1 className="text-xl font-serif font-bold tracking-tight">Code Intelligence Report</h1>
              <p className="text-xs font-sans text-muted-foreground tracking-wider uppercase mt-0.5">ID: {reviewId?.substring(0, 8)}</p>
            </div>
          </div>
          
          {results && (
            <div className="flex items-center gap-8">
              <div className="hidden md:flex items-center gap-6">
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-0.5">Findings</p>
                  <p className="font-serif font-bold text-lg leading-none">{results.total_findings}</p>
                </div>
                <div className="h-8 w-[1px] bg-border/60"></div>
                <div className="flex gap-3">
                  {results.severity_counts.critical > 0 && (
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1">Critical</span>
                      <div className="px-2.5 py-0.5 rounded-full bg-red-50 text-red-700 text-xs font-bold border border-red-100">
                        {results.severity_counts.critical}
                      </div>
                    </div>
                  )}
                  {results.severity_counts.high > 0 && (
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1">High</span>
                      <div className="px-2.5 py-0.5 rounded-full bg-orange-50 text-orange-700 text-xs font-bold border border-orange-100">
                        {results.severity_counts.high}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <Button size="sm" className="bg-primary text-primary-foreground shadow-sm px-4">
                Export PDF
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-6 pt-4 pb-8">
        {results && (
          <div className="grid lg:grid-cols-12 gap-8 items-start">
            {/* Sidebar: Navigation & File Tree */}
            <div className="lg:col-span-3 space-y-6 lg:sticky lg:top-24">
              <Card className="border-none shadow-sm overflow-hidden bg-card/50 backdrop-blur-sm">
                <CardHeader className="pb-3 border-b border-border/40">
                  <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground">Exploration</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <FileTree
                    files={[
                      { name: 'src', path: 'src', type: 'directory', children: [
                        { name: 'main.py', path: 'src/main.py', type: 'file' },
                        { name: 'utils.py', path: 'src/utils.py', type: 'file' },
                      ]}
                    ]}
                    onFileSelect={handleFileSelect}
                    selectedFile={selectedFile || undefined}
                  />
                </CardContent>
              </Card>

              {/* Summary Stats Card */}
              <Card className="border-none shadow-sm bg-accent/5 overflow-hidden">
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs uppercase tracking-widest text-accent/80">Health Overview</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-card/50 backdrop-blur-sm rounded-lg border border-accent/10 shadow-sm">
                      <p className="text-[10px] text-muted-foreground uppercase mb-1">Coverage</p>
                      <p className="text-xl font-serif font-bold">94%</p>
                    </div>
                    <div className="p-3 bg-card/50 backdrop-blur-sm rounded-lg border border-accent/10 shadow-sm">
                      <p className="text-[10px] text-muted-foreground uppercase mb-1">Stability</p>
                      <p className="text-xl font-serif font-bold">High</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-9">
              <Tabs defaultValue="findings" className="w-full">
                <div className="flex items-center justify-between mb-6 border-b border-border/40 pb-px">
                  <TabsList className="bg-transparent h-auto p-0 gap-8 rounded-none border-b-0">
                    <TabsTrigger 
                      value="findings" 
                      className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 py-3 text-sm font-medium transition-all"
                    >
                      <LayoutGrid className="h-4 w-4 mr-2" />
                      Detailed Findings
                    </TabsTrigger>
                    <TabsTrigger 
                      value="code" 
                      className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 py-3 text-sm font-medium transition-all"
                    >
                      <FileCode className="h-4 w-4 mr-2" />
                      Source Explorer
                    </TabsTrigger>
                    <TabsTrigger 
                      value="summary" 
                      className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 py-3 text-sm font-medium transition-all"
                    >
                      <ScrollText className="h-4 w-4 mr-2" />
                      Executive Summary
                    </TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="findings" className="mt-0 focus-visible:outline-none">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-2xl font-serif italic text-muted-foreground">Architectural observations</h3>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="text-xs h-8">All Agents</Button>
                        <Button variant="outline" size="sm" className="text-xs h-8">All Severities</Button>
                      </div>
                    </div>
                    <AgentComments
                      findings={results.findings}
                      onFindingClick={handleFindingClick}
                    />
                  </div>
                </TabsContent>

                <TabsContent value="code" className="mt-0 focus-visible:outline-none">
                  <Card className="border-none shadow-xl overflow-hidden min-h-[600px] bg-[#1e1e1e]">
                    {selectedFile ? (
                      <div className="flex flex-col h-full">
                        <div className="px-4 py-2 bg-[#252526] border-b border-white/5 flex items-center justify-between">
                          <span className="text-xs text-gray-400 font-mono">{selectedFile}</span>
                          <span className="text-[10px] text-gray-500 uppercase tracking-widest">{getFileFindings(selectedFile).length} issues found</span>
                        </div>
                        <div className="flex-grow">
                          <CodeViewer
                            code={fileContent}
                            language="python"
                            findings={getFileFindings(selectedFile)}
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-[600px] text-gray-500 space-y-4">
                        <FileCode className="h-16 w-16 opacity-20" />
                        <p className="font-serif italic text-lg opacity-40">Select a component for inspection</p>
                      </div>
                    )}
                  </Card>
                </TabsContent>

                <TabsContent value="summary" className="mt-0 focus-visible:outline-none">
                  <div className="grid md:grid-cols-2 gap-8">
                    <Card className="border-none shadow-sm bg-card/50 backdrop-blur-sm">
                      <CardHeader>
                        <CardTitle className="font-serif">Severity Distribution</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-6 py-4">
                          {[
                            { label: 'Critical', count: results.severity_counts.critical, color: 'bg-red-500', text: 'text-red-500' },
                            { label: 'High Risk', count: results.severity_counts.high, color: 'bg-orange-500', text: 'text-orange-500' },
                            { label: 'Medium', count: results.severity_counts.medium, color: 'bg-yellow-500', text: 'text-yellow-500' },
                            { label: 'Low', count: results.severity_counts.low, color: 'bg-blue-500', text: 'text-blue-500' },
                            { label: 'Informational', count: results.severity_counts.info, color: 'bg-gray-400', text: 'text-gray-400' },
                          ].map((item) => (
                            <div key={item.label} className="space-y-2">
                              <div className="flex justify-between items-end">
                                <span className="text-sm font-medium">{item.label}</span>
                                <span className={`text-lg font-serif font-bold ${item.text}`}>{item.count || 0}</span>
                              </div>
                              <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                <div 
                                  className={`h-full ${item.color}`} 
                                  style={{ width: `${((item.count || 0) / (results.total_findings || 1)) * 100}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-none shadow-sm bg-card/50 backdrop-blur-sm">
                      <CardHeader>
                        <CardTitle className="font-serif">Agent Contributions</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-8 py-4">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                              <Shield className="h-5 w-5" />
                            </div>
                            <div className="flex-grow">
                              <p className="text-sm font-bold">Security Agent</p>
                              <p className="text-xs text-muted-foreground">Scanning for OWASP vulnerabilities</p>
                            </div>
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-purple-50 flex items-center justify-center text-purple-600">
                              <Code2 className="h-5 w-5" />
                            </div>
                            <div className="flex-grow">
                              <p className="text-sm font-bold">Architect Agent</p>
                              <p className="text-xs text-muted-foreground">Analyzing patterns and structure</p>
                            </div>
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-amber-600">
                              <Zap className="h-5 w-5" />
                            </div>
                            <div className="flex-grow">
                              <p className="text-sm font-bold">Performance Agent</p>
                              <p className="text-xs text-muted-foreground">Optimizing runtime efficiency</p>
                            </div>
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
