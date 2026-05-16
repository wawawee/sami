#!/usr/bin/env python3
"""
Codebase Vectorization System for Agent Context Loading
Creates semantic chunks of code for efficient retrieval within token limits
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import ast
import re

# Configuration
CODEBASE_ROOT = Path(".")
VECTOR_ROOT = Path("./vector")
EMBEDDINGS_DIR = VECTOR_ROOT / "embeddings"
CHUNKS_DIR = VECTOR_ROOT / "chunks"
CONFIG_FILE = VECTOR_ROOT / "config.json"

# File extensions to process
CODE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.html': 'html',
    '.css': 'css',
    '.md': 'markdown',
    '.txt': 'text',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml'
}

# Directories to exclude
EXCLUDE_DIRS = {
    'node_modules', '__pycache__', '.git', '.vscode', '.idea',
    'venv', '.venv', 'dist', 'build', '.next', '.nuxt',
    'coverage', '.cache', '.parcel'
}

def should_process_file(file_path: Path) -> bool:
    """Check if a file should be processed for vectorization"""
    # Check extension
    if file_path.suffix.lower() not in CODE_EXTENSIONS:
        return False
    
    # Check if in excluded directory
    for parent in file_path.parents:
        if parent.name in EXCLUDE_DIRS:
            return False
    
    # Check file size (skip very large files)
    try:
        if file_path.stat().st_size > 1024 * 1024:  # 1MB
            return False
    except OSError:
        return False
    
    return True

def extract_semantic_chunks(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract semantic chunks from a file based on its language
    Returns list of chunks with metadata
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, IOError):
        return []
    
    chunks = []
    lang = CODE_EXTENSIONS.get(file_path.suffix.lower(), 'text')
    
    if lang == 'python':
        chunks.extend(extract_python_chunks(content, file_path))
    elif lang in ['javascript', 'typescript']:
        chunks.extend(extract_js_ts_chunks(content, file_path))
    elif lang == 'markdown':
        chunks.extend(extract_markdown_chunks(content, file_path))
    else:
        # Fallback: chunk by paragraphs or lines
        chunks.extend(extract_generic_chunks(content, file_path))
    
    return chunks

def extract_python_chunks(content: str, file_path: Path) -> List[Dict[str, Any]]:
    """Extract semantic chunks from Python code"""
    chunks = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # If we can't parse, fall back to generic chunking
        return extract_generic_chunks(content, file_path)
    
    # Extract functions and classes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            try:
                # Get the source code for this node
                start_line = node.lineno - 1  # Convert to 0-indexed
                end_line = getattr(node, 'end_lineno', start_line + 10) - 1
                
                # Try to get end_lineno if available (Python 3.8+)
                if hasattr(node, 'end_lineno'):
                    end_line = node.end_lineno - 1
                else:
                    # Estimate end line - this is approximate
                    end_line = min(start_line + 20, len(content.split('\n')))
                
                lines = content.split('\n')[start_line:end_line+1]
                chunk_content = '\n'.join(lines)
                
                # Create chunk
                chunk = {
                    'content': chunk_content,
                    'metadata': {
                        'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                        'file_type': 'python',
                        'chunk_type': node.__class__.__name__,
                        'name': getattr(node, 'name', 'anonymous'),
                        'start_line': start_line + 1,  # Convert back to 1-indexed
                        'end_line': end_line + 1,
                        'size': len(chunk_content),
                        'hash': hashlib.md5(chunk_content.encode()).hexdigest()[:8]
                    }
                }
                chunks.append(chunk)
            except (AttributeError, IndexError):
                continue
    
    # If no functions/classes found, fall back to generic
    if not chunks:
        chunks.extend(extract_generic_chunks(content, file_path))
    
    return chunks

def extract_js_ts_chunks(content: str, file_path: Path) -> List[Dict[str, Any]]:
    """Extract semantic chunks from JavaScript/TypeScript code"""
    chunks = []
    
    # Simple regex-based extraction for functions, classes, etc.
    # This is a simplified version - in practice you'd use a proper parser
    
    # Extract functions
    func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*{'
    for match in re.finditer(func_pattern, content):
        start_pos = match.start()
        # Find matching closing brace (simplified)
        brace_count = 0
        in_string = False
        escape_next = False
        end_pos = start_pos
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' or char == "'" or char == '`':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        if end_pos > start_pos:
            chunk_content = content[start_pos:end_pos]
            # Extract function name
            name_match = re.search(r'function\s+(\w+)', chunk_content)
            name = name_match.group(1) if name_match else 'anonymous'
            
            chunk = {
                'content': chunk_content,
                'metadata': {
                    'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                    'file_type': 'javascript-typescript',
                    'chunk_type': 'function',
                    'name': name,
                    'start_line': content[:start_pos].count('\n') + 1,
                    'end_line': content[:end_pos].count('\n') + 1,
                    'size': len(chunk_content),
                    'hash': hashlib.md5(chunk_content.encode()).hexdigest()[:8]
                }
            }
            chunks.append(chunk)
    
    # Extract classes
    class_pattern = r'(?:export\s+)?class\s+(\w+)\s*{'
    for match in re.finditer(class_pattern, content):
        start_pos = match.start()
        # Find matching closing brace (simplified)
        brace_count = 0
        in_string = False
        escape_next = False
        end_pos = start_pos
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' or char == "'" or char == '`':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        if end_pos > start_pos:
            chunk_content = content[start_pos:end_pos]
            # Extract class name
            name_match = re.search(r'class\s+(\w+)', chunk_content)
            name = name_match.group(1) if name_match else 'anonymous'
            
            chunk = {
                'content': chunk_content,
                'metadata': {
                    'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                    'file_type': 'javascript-typescript',
                    'chunk_type': 'class',
                    'name': name,
                    'start_line': content[:start_pos].count('\n') + 1,
                    'end_line': content[:end_pos].count('\n') + 1,
                    'size': len(chunk_content),
                    'hash': hashlib.md5(chunk_content.encode()).hexdigest()[:8]
                }
            }
            chunks.append(chunk)
    
    # If no chunks found, fall back to generic
    if not chunks:
        chunks.extend(extract_generic_chunks(content, file_path))
    
    return chunks

def extract_markdown_chunks(content: str, file_path: Path) -> List[Dict[str, Any]]:
    """Extract semantic chunks from Markdown"""
    chunks = []
    
    # Split by headers
    sections = re.split(r'\n(?=#{1,6}\s)', content)
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        
        # Try to extract header
        header_match = re.match(r'^(#{1,6})\s*(.+)$', section.split('\n')[0])
        header_level = len(header_match.group(1)) if header_match else 0
        header_text = header_match.group(2) if header_match else f"Section {i+1}"
        
        chunk = {
            'content': section.strip(),
            'metadata': {
                'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                'file_type': 'markdown',
                'chunk_type': 'section',
                'header': header_text,
                'header_level': header_level,
                'start_line': content[:content.find(section)].count('\n') + 1 if section in content else 1,
                'end_line': content[:content.find(section) + len(section)].count('\n') if section in content else len(section.split('\n')),
                'size': len(section),
                'hash': hashlib.md5(section.encode()).hexdigest()[:8]
            }
        }
        chunks.append(chunk)
    
    # If no sections found, treat whole file as one chunk
    if not chunks and content.strip():
        chunks.append({
            'content': content.strip(),
            'metadata': {
                'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                'file_type': 'markdown',
                'chunk_type': 'document',
                'size': len(content),
                'hash': hashlib.md5(content.encode()).hexdigest()[:8]
            }
        })
    
    return chunks

def extract_generic_chunks(content: str, file_path: Path) -> List[Dict[str, Any]]:
    """Generic chunking by paragraphs or fixed size"""
    chunks = []
    
    # Try to split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', content)
    
    current_chunk = ""
    current_start = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph would make chunk too large, save current and start new
        if len(current_chunk) + len(para) > 1000 and current_chunk:  # ~1000 char limit
            chunk = {
                'content': current_chunk.strip(),
                'metadata': {
                    'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                    'file_type': 'generic',
                    'chunk_type': 'paragraph_group',
                    'start_line': content[:current_start].count('\n') + 1,
                    'end_line': content[:current_start + len(current_chunk)].count('\n'),
                    'size': len(current_chunk),
                    'hash': hashlib.md5(current_chunk.encode()).hexdigest()[:8]
                }
            }
            chunks.append(chunk)
            current_chunk = para
            current_start = content.find(para, current_start)
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                current_start = content.find(para, current_start)
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunk = {
            'content': current_chunk.strip(),
            'metadata': {
                'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                'file_type': 'generic',
                'chunk_type': 'paragraph_group',
                'start_line': content[:current_start].count('\n') + 1,
                'end_line': content[:current_start + len(current_chunk)].count('\n'),
                'size': len(current_chunk),
                'hash': hashlib.md5(current_chunk.encode()).hexdigest()[:8]
            }
        }
        chunks.append(chunk)
    
    # If still no chunks, split by lines
    if not chunks:
        lines = content.split('\n')
        for i in range(0, len(lines), 20):  # 20 lines per chunk
            chunk_lines = lines[i:i+20]
            chunk_content = '\n'.join(chunk_lines)
            if chunk_content.strip():
                chunk = {
                    'content': chunk_content,
                    'metadata': {
                        'file_path': str(file_path.relative_to(CODEBASE_ROOT)),
                        'file_type': 'generic',
                        'chunk_type': 'line_group',
                        'start_line': i + 1,
                        'end_line': min(i + 20, len(lines)),
                        'size': len(chunk_content),
                        'hash': hashlib.md5(chunk_content.encode()).hexdigest()[:8]
                    }
                }
                chunks.append(chunk)
    
    return chunks

def process_codebase():
    """Process the entire codebase and create chunks for vectorization"""
    logger.info("Starting codebase vectorization...")
    # Create directories
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    processed_files = 0
    
    # Walk through codebase
    for root, dirs, files in os.walk(CODEBASE_ROOT):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            
            if should_process_file(file_path):
                logger.info(f"Processing: {file_path}")
                chunks = extract_semantic_chunks(file_path)
                all_chunks.extend(chunks)
                processed_files += 1
    
    logger.info(f"Processed {processed_files} files, created {len(all_chunks)} chunks")
    # Save chunks to file
    chunks_file = CHUNKS_DIR / "codebase_chunks.json"
    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2)
    
    # Create configuration
    config = {
        "version": "1.0.0",
        "created": "2026-05-16",
        "total_files": processed_files,
        "total_chunks": len(all_chunks),
        "chunking_strategy": "semantic",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",  # Example
        "vector_dimension": 384,
        "similarity_metric": "cosine",
        "max_tokens_per_context": 4000,  # For agent context window
        "retrieval_top_k": 5,  # Number of chunks to retrieve per query
        "chunks_file": str(chunks_file.relative_to(CODEBASE_ROOT)),
        "embeddings_dir": str(EMBEDDINGS_DIR.relative_to(CODEBASE_ROOT))
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Vectorization complete! Chunks saved to {chunks_file}")
    logger.info(f"Configuration saved to {CONFIG_FILE}")
    return all_chunks

if __name__ == "__main__":
    process_codebase()