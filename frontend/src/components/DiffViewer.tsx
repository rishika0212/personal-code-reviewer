import type { LineDiff } from '@/types/review'
import { Plus, Minus } from 'lucide-react'

interface DiffViewerProps {
  lineDiff: LineDiff[]
  fileName: string
}

export default function DiffViewer({ lineDiff, fileName }: DiffViewerProps) {
  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] rounded-lg overflow-hidden border border-white/5 font-mono text-sm">
      <div className="px-4 py-2 bg-[#252526] border-b border-white/5 flex items-center justify-between">
        <span className="text-xs text-gray-400 font-mono">{fileName}</span>
      </div>
      <div className="flex-grow overflow-auto p-4 custom-scrollbar">
        <table className="w-full border-collapse">
          <tbody>
            {lineDiff.map((line, idx) => {
              const isAdded = line.type === 'added'
              const isRemoved = line.type === 'removed'
              
              return (
                <tr 
                  key={idx} 
                  className={`${
                    isAdded ? 'bg-green-900/30 text-green-200' : 
                    isRemoved ? 'bg-red-900/30 text-red-200' : 
                    'text-gray-300'
                  } hover:bg-white/5 transition-colors`}
                >
                  <td className="w-12 text-right pr-4 py-0.5 text-gray-600 select-none border-r border-white/5 text-[10px]">
                    {line.line_number}
                  </td>
                  <td className="w-6 pl-2 py-0.5 select-none">
                    {isAdded ? <Plus className="h-3 w-3 text-green-500" /> : 
                     isRemoved ? <Minus className="h-3 w-3 text-red-500" /> : 
                     null}
                  </td>
                  <td className="pl-2 py-0.5 whitespace-pre break-all">
                    {line.content}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
