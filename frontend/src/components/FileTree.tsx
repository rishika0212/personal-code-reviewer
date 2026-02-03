import { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen, FileCode, FileText, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
}

interface FileTreeProps {
  files: FileNode[]
  onFileSelect: (path: string) => void
  selectedFile?: string
}

interface TreeNodeProps {
  node: FileNode
  onFileSelect: (path: string) => void
  selectedFile?: string
  depth?: number
}

function getFileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (['py', 'js', 'ts', 'tsx', 'cpp', 'c', 'go', 'rust', 'rb', 'php'].includes(ext || '')) {
    return <FileCode className="h-3.5 w-3.5" />
  }
  if (['json', 'yaml', 'yml', 'toml', 'config'].includes(ext || '')) {
    return <Settings className="h-3.5 w-3.5" />
  }
  return <FileText className="h-3.5 w-3.5" />
}

function TreeNode({ node, onFileSelect, selectedFile, depth = 0 }: TreeNodeProps) {
  const [isOpen, setIsOpen] = useState(depth < 2)
  const isSelected = selectedFile === node.path
  const isDirectory = node.type === 'directory'

  const handleClick = () => {
    if (isDirectory) {
      setIsOpen(!isOpen)
    } else {
      onFileSelect(node.path)
    }
  }

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 cursor-pointer rounded-sm transition-all font-sans group relative mb-[1px]",
          isSelected 
            ? "bg-accent/5 text-accent font-medium" 
            : "text-foreground/70 hover:bg-secondary/40 hover:text-foreground"
        )}
        style={{ paddingLeft: `${depth * 12 + 12}px` }}
        onClick={handleClick}
      >
        {isSelected && (
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-3 bg-accent rounded-full" />
        )}
        <div className="flex items-center justify-center w-4 h-4">
          {isDirectory ? (
            isOpen ? (
              <ChevronDown className="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity" />
            ) : (
              <ChevronRight className="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity" />
            )
          ) : null}
        </div>
        
        <div className={cn(
          "flex-shrink-0",
          isSelected ? "text-accent" : "text-muted-foreground/60 group-hover:text-muted-foreground"
        )}>
          {isDirectory ? (
            isOpen ? <FolderOpen className="h-4 w-4" /> : <Folder className="h-4 w-4" />
          ) : (
            getFileIcon(node.name)
          )}
        </div>
        
        <span className="text-xs truncate tracking-tight">{node.name}</span>
      </div>
      
      {isDirectory && isOpen && node.children && (
        <div className="mt-0.5">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              onFileSelect={onFileSelect}
              selectedFile={selectedFile}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FileTree({ files, onFileSelect, selectedFile }: FileTreeProps) {
  return (
    <div className="py-2 bg-transparent overflow-auto max-h-[600px] scrollbar-hide">
      {files.map((node) => (
        <TreeNode
          key={node.path}
          node={node}
          onFileSelect={onFileSelect}
          selectedFile={selectedFile}
        />
      ))}
    </div>
  )
}
