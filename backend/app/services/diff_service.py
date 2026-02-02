from typing import List, Dict, Tuple
import difflib


class DiffService:
    """Service for computing and displaying code diffs"""
    
    @staticmethod
    def compute_diff(
        original: str,
        modified: str,
        context_lines: int = 3
    ) -> str:
        """Compute a unified diff between two code versions"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile='original',
            tofile='modified',
            n=context_lines
        )
        
        return ''.join(diff)
    
    @staticmethod
    def compute_line_diff(
        original: str,
        modified: str
    ) -> List[Dict[str, any]]:
        """Compute line-by-line diff with change types"""
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        matcher = difflib.SequenceMatcher(
            None,
            original_lines,
            modified_lines
        )
        
        result = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for line in original_lines[i1:i2]:
                    result.append({
                        'type': 'unchanged',
                        'content': line,
                        'line_number': len(result) + 1
                    })
            elif tag == 'delete':
                for line in original_lines[i1:i2]:
                    result.append({
                        'type': 'removed',
                        'content': line,
                        'line_number': len(result) + 1
                    })
            elif tag == 'insert':
                for line in modified_lines[j1:j2]:
                    result.append({
                        'type': 'added',
                        'content': line,
                        'line_number': len(result) + 1
                    })
            elif tag == 'replace':
                for line in original_lines[i1:i2]:
                    result.append({
                        'type': 'removed',
                        'content': line,
                        'line_number': len(result) + 1
                    })
                for line in modified_lines[j1:j2]:
                    result.append({
                        'type': 'added',
                        'content': line,
                        'line_number': len(result) + 1
                    })
        
        return result
    
    @staticmethod
    def get_changed_lines(
        original: str,
        modified: str
    ) -> Tuple[List[int], List[int]]:
        """Get lists of added and removed line numbers"""
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        matcher = difflib.SequenceMatcher(
            None,
            original_lines,
            modified_lines
        )
        
        removed = []
        added = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('delete', 'replace'):
                removed.extend(range(i1 + 1, i2 + 1))
            if tag in ('insert', 'replace'):
                added.extend(range(j1 + 1, j2 + 1))
        
        return removed, added
    
    @staticmethod
    def highlight_changes(
        original: str,
        modified: str
    ) -> Dict[str, str]:
        """Return both versions with inline change markers"""
        # This is a simplified version - could be enhanced with
        # character-level diff highlighting
        diff = DiffService.compute_diff(original, modified)
        
        return {
            'original': original,
            'modified': modified,
            'diff': diff
        }
