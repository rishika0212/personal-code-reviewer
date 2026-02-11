import { useNavigate } from 'react-router-dom'
import { Code2, Shield, Zap, Github } from 'lucide-react'
import RepoUploader from '@/components/RepoUploader'
import { startReview } from '@/api/reviewApi'

export default function Home() {
  const navigate = useNavigate()

  const handleRepoUploaded = async (repoId: string) => {
    try {
      const { review_id } = await startReview(repoId)
      navigate(`/review/${review_id}`)
    } catch (error) {
      console.error('Failed to start review:', error)
    }
  }

  const features = [
    {
      icon: <Code2 className="h-6 w-6" />,
      title: 'Architectural Analysis',
      description: 'Sophisticated evaluation of code structure, design patterns, and systemic logic.'
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: 'Security Assurance',
      description: 'Rigorous detection of vulnerabilities and adherence to security best practices.'
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: 'Performance Insight',
      description: 'Precise identification of bottlenecks and elegant optimization strategies.'
    }
  ]

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Decorative background elements - Removed blurs for performance */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-accent/[0.02] pointer-events-none"></div>
      <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-accent/5 rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[10%] left-[-5%] w-[30%] h-[30%] bg-accent/3 rounded-full pointer-events-none"></div>
      
      <main className="flex-grow flex items-center justify-center relative z-10">
        <div className="container mx-auto px-6">
          {/* Hero Section */}
          <div className="max-w-4xl mx-auto text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-secondary-foreground text-xs font-medium tracking-wider uppercase mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
              <Github className="h-3 w-3" />
              <span>AI-Driven Review Engine</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-serif mb-8 tracking-tight leading-tight animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-200">
              CodeReviewX
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto font-sans leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
              Refined code review for the discerning developer.
            </p>
          </div>

          {/* Upload Section */}
          <div className="max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-500">
            <div className="relative group">
              <div className="absolute -inset-1 bg-accent/5 rounded-lg opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative">
                <RepoUploader onRepoUploaded={handleRepoUploaded} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
