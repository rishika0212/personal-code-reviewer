import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Code2, Shield, Zap, Github } from 'lucide-react'
import RepoUploader from '@/components/RepoUploader'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { startReview } from '@/api/reviewApi'

export default function Home() {
  const navigate = useNavigate()
  const [isStartingReview, setIsStartingReview] = useState(false)

  const handleRepoUploaded = async (repoId: string, repoName: string) => {
    setIsStartingReview(true)
    try {
      const { review_id } = await startReview(repoId)
      navigate(`/review/${review_id}`)
    } catch (error) {
      console.error('Failed to start review:', error)
      setIsStartingReview(false)
    }
  }

  const features = [
    {
      icon: <Code2 className="h-8 w-8 text-blue-500" />,
      title: 'Bug Detection',
      description: 'Find potential bugs, logic errors, and code smells automatically'
    },
    {
      icon: <Shield className="h-8 w-8 text-green-500" />,
      title: 'Security Analysis',
      description: 'Detect security vulnerabilities following OWASP guidelines'
    },
    {
      icon: <Zap className="h-8 w-8 text-yellow-500" />,
      title: 'Performance Review',
      description: 'Identify performance bottlenecks and optimization opportunities'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Github className="h-12 w-12" />
            <h1 className="text-4xl font-bold">Coder</h1>
          </div>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            AI-powered code review system that analyzes your code for bugs, 
            security vulnerabilities, and performance issues.
          </p>
        </div>

        {/* Upload Section */}
        <div className="flex justify-center mb-16">
          <RepoUploader onRepoUploaded={handleRepoUploaded} />
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {features.map((feature, index) => (
            <Card key={index} className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-2">
                  {feature.icon}
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* How it works */}
        <div className="mt-16 max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">How it works</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                1
              </div>
              <p>Upload your GitHub repository URL</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                2
              </div>
              <p>Our AI agents analyze your code in parallel</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                3
              </div>
              <p>Get detailed findings with actionable suggestions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
