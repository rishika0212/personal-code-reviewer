import { useState } from 'react'
import { Upload, Github, Loader2 } from 'lucide-react'
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
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Github className="h-5 w-5" />
          Upload Repository
        </CardTitle>
        <CardDescription>
          Enter a GitHub repository URL to start the code review
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={loading}
            />
          </div>
          
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          
          <Button type="submit" disabled={loading || !url.trim()} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Cloning Repository...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Start Review
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
