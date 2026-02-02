import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import FileTree from '@/components/FileTree'
import CodeViewer from '@/components/CodeViewer'
import AgentComments from '@/components/AgentComments'
import SeverityBadge from '@/components/SeverityBadge'
import { useReviewStatus } from '@/hooks/useReviewStatus'
import { getReviewResults } from '@/api/reviewApi'
import type { ReviewResponse, ReviewFinding } from '@/types/review'

export default function Review() {
  const { reviewId } = useParams<{ reviewId: string }>()
  const { status, progress, error: statusError } = useReviewStatus(reviewId!)
  const [results, setResults] = useState<ReviewResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (status === 'completed' && reviewId) {
      fetchResults()
    }
  }, [status, reviewId])

  const fetchResults = async () => {
    if (!reviewId) return
    setLoading(true)
    try {
      const data = await getReviewResults(reviewId)
      setResults(data)
    } catch (err) {
      console.error('Failed to fetch results:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (path: string) => {
    setSelectedFile(path)
    // In a real app, fetch file content from API
    setFileContent('// File content would be loaded here')
  }

  const handleFindingClick = (finding: ReviewFinding) => {
    setSelectedFile(finding.file_path)
    // Scroll to line in code viewer
  }

  const getFileFindings = (filePath: string): ReviewFinding[] => {
    if (!results) return []
    return results.findings.filter(f => f.file_path === filePath)
  }

  // Show loading state
  if (status === 'pending' || status === 'processing') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-center">Analyzing Code</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
            </div>
            <div className="space-y-2">
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-center text-sm text-muted-foreground">
                {progress}% complete
              </p>
            </div>
            <p className="text-center text-sm text-muted-foreground">
              Our AI agents are reviewing your code...
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Show error state
  if (status === 'failed' || statusError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-center text-destructive">Review Failed</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-muted-foreground mb-4">
              {statusError || 'An error occurred during the review'}
            </p>
            <Link to="/">
              <Button>Try Again</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="font-bold">Code Review</h1>
              <p className="text-sm text-muted-foreground">Review ID: {reviewId}</p>
            </div>
          </div>
          
          {results && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Total Issues</p>
                <p className="font-bold text-lg">{results.total_findings}</p>
              </div>
              <div className="flex gap-2">
                {results.severity_counts.critical > 0 && (
                  <SeverityBadge severity="critical" />
                )}
                {results.severity_counts.high > 0 && (
                  <SeverityBadge severity="high" />
                )}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {results && (
          <div className="grid lg:grid-cols-4 gap-6">
            {/* File Tree */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <FileTree
                    files={[
                      // Mock file tree - in real app, fetch from API
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
            </div>

            {/* Main Panel */}
            <div className="lg:col-span-3">
              <Tabs defaultValue="findings">
                <TabsList>
                  <TabsTrigger value="findings">
                    Findings ({results.total_findings})
                  </TabsTrigger>
                  <TabsTrigger value="code">Code View</TabsTrigger>
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                </TabsList>

                <TabsContent value="findings" className="mt-4">
                  <AgentComments
                    findings={results.findings}
                    onFindingClick={handleFindingClick}
                  />
                </TabsContent>

                <TabsContent value="code" className="mt-4">
                  {selectedFile ? (
                    <CodeViewer
                      code={fileContent}
                      language="python"
                      fileName={selectedFile}
                      findings={getFileFindings(selectedFile)}
                    />
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      Select a file from the tree to view its code
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="summary" className="mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Review Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-5 gap-4 text-center">
                        <div>
                          <p className="text-2xl font-bold text-red-600">
                            {results.severity_counts.critical || 0}
                          </p>
                          <p className="text-sm text-muted-foreground">Critical</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-orange-500">
                            {results.severity_counts.high || 0}
                          </p>
                          <p className="text-sm text-muted-foreground">High</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-yellow-500">
                            {results.severity_counts.medium || 0}
                          </p>
                          <p className="text-sm text-muted-foreground">Medium</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-blue-500">
                            {results.severity_counts.low || 0}
                          </p>
                          <p className="text-sm text-muted-foreground">Low</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-gray-500">
                            {results.severity_counts.info || 0}
                          </p>
                          <p className="text-sm text-muted-foreground">Info</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
