import { useState, useEffect, useCallback } from 'react'
import { getReviewStatus } from '@/api/reviewApi'

interface UseReviewStatusResult {
  status: string
  progress: number
  message: string | null
  error: string | null
  refetch: () => void
}

export function useReviewStatus(reviewId: string): UseReviewStatusResult {
  const [status, setStatus] = useState<string>('pending')
  const [progress, setProgress] = useState<number>(0)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!reviewId) return
    
    try {
      const data = await getReviewStatus(reviewId)
      setStatus(data.status)
      setProgress(data.progress)
      setMessage(data.message || null)
      setError(data.error || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status')
    }
  }, [reviewId])

  useEffect(() => {
    // Initial fetch
    let isMounted = true
    const initFetch = async () => {
      if (isMounted) {
        await fetchStatus()
      }
    }
    initFetch()
    return () => { isMounted = false }
  }, [fetchStatus])

  useEffect(() => {
    // Poll for status updates while processing
    if (status !== 'pending' && status !== 'processing') return

    let timer: NodeJS.Timeout
    
    const poll = async () => {
      await fetchStatus()
      if (status === 'pending' || status === 'processing') {
        timer = setTimeout(poll, 5000) // FIX 5: Reduce polling to 5 seconds
      }
    }

    timer = setTimeout(poll, 5000)

    return () => clearTimeout(timer)
  }, [fetchStatus, status])

  return { status, progress, message, error, refetch: fetchStatus }
}
