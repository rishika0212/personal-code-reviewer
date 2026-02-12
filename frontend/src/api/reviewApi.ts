import axios from 'axios'
import type { ReviewResponse, ReviewStatus, RepoInfo, FileNode, PatchResponse } from '@/types/review'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function uploadGitHubRepo(url: string): Promise<RepoInfo> {
  const response = await api.post<RepoInfo>('/repo/github', { url })
  return response.data
}

export async function startReview(repoId: string): Promise<{ review_id: string }> {
  const response = await api.post<{ review_id: string }>('/review/', { repo_id: repoId })
  return response.data
}

export async function getReviewStatus(reviewId: string): Promise<ReviewStatus> {
  const response = await api.get<ReviewStatus>(`/review/status/${reviewId}`)
  return response.data
}

export async function getReviewResults(reviewId: string): Promise<ReviewResponse> {
  const response = await api.get<ReviewResponse>(`/review/${reviewId}`)
  return response.data
}

export async function getRepoFiles(repoId: string): Promise<{ files: FileNode[] }> {
  const response = await api.get<{ files: FileNode[] }>(`/repo/files/${repoId}`)
  return response.data
}

export async function getFileContent(repoId: string, path: string): Promise<{ content: string }> {
  const response = await api.get<{ content: string }>(`/repo/content/${repoId}`, { params: { path } })
  return response.data
}

export async function generatePatch(reviewId: string, findingIds: string[]): Promise<PatchResponse> {
  const response = await api.post<PatchResponse>('/review/patch', { review_id: reviewId, finding_ids: findingIds })
  return response.data
}

export async function applyPatches(reviewId: string, patches: Record<string, string>): Promise<{ success: boolean }> {
  const response = await api.post<{ success: boolean }>('/review/apply', { review_id: reviewId, patches })
  return response.data
}

export async function pushToGitHub(reviewId: string, title?: string, body?: string): Promise<{ pr_url: string }> {
  const response = await api.post<{ pr_url: string }>('/review/push', { 
    review_id: reviewId, 
    title, 
    body 
  })
  return response.data
}
