import { useState, useEffect, useCallback } from 'react'
import { getReviewStatus } from '@/api/reviewApi'

interface UseReviewStatusResult {
  status: string
  progress: number
  error: string | null
  refetch: () => void
}

export function useReviewStatus(reviewId: string): UseReviewStatusResult {
  const [status, setStatus] = useState<string>('pending')
  const [progress, setProgress] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!reviewId) return
    
    try {
      const data = await getReviewStatus(reviewId)
      setStatus(data.status)
      setProgress(data.progress)
      setError(data.error || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status')
    }
  }, [reviewId])

  useEffect(() => {
    fetchStatus()

    // Poll for status updates while processing
    const interval = setInterval(() => {
      if (status === 'pending' || status === 'processing') {
        fetchStatus()
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [fetchStatus, status])

  return { status, progress, error, refetch: fetchStatus }
}
