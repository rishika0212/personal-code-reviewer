export interface ReviewFinding {
  id: string
  agent_name: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  category: string
  title: string
  description: string
  file_path: string
  start_line: number
  end_line: number
  suggestion: string
  code_snippet: string
}

export interface ReviewResponse {
  review_id: string
  repo_id: string
  status: string
  total_findings: number
  severity_counts: {
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
  findings: ReviewFinding[]
}

export interface ReviewStatus {
  review_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message?: string
  error?: string
}

export interface RepoInfo {
  repo_id: string
  name: string
  url: string
  files_count: number
  languages: string[]
}

export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
}
