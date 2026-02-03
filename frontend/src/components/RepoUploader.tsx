import { useState } from 'react'
import { Github, Loader2, ArrowRight } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { uploadGitHubRepo } from '@/api/reviewApi'

interface RepoUploaderProps {
  onRepoUploaded: (repoId: string, repoName: string) => void
}

export default function RepoUploader({ onRepoUploaded }: RepoUploaderProps) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setError(null)

    try {
      const repoInfo = await uploadGitHubRepo(url)
      onRepoUploaded(repoInfo.repo_id, repoInfo.name)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload repository')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="border-none shadow-2xl bg-card overflow-hidden">
      <CardHeader className="pb-4">
        <CardTitle className="font-serif text-2xl">
          Repository Analysis
        </CardTitle>
        <CardDescription className="font-sans text-base">
          Provide your GitHub URL to initiate an architectural review.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative group">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-accent transition-colors">
              <Github className="h-5 w-5" />
            </div>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/username/repository"
              className="w-full pl-12 pr-4 py-4 bg-secondary/50 border-none rounded-lg text-foreground placeholder:text-muted-foreground focus:ring-1 focus:ring-accent transition-all font-sans text-lg"
              disabled={loading}
            />
          </div>
          
          {error && (
            <div className="px-4 py-3 rounded-lg bg-destructive/5 border border-destructive/20 text-destructive text-sm font-sans">
              {error}
            </div>
          )}
          
          <Button 
            type="submit" 
            disabled={loading || !url.trim()} 
            className="w-full py-6 text-lg font-medium tracking-wide transition-all hover:translate-y-[-1px] active:translate-y-[0px] shadow-lg hover:shadow-accent/20"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Processing Repository...
              </>
            ) : (
              <>
                Analyze Codebase
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
