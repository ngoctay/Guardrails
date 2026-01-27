"""Performance optimization features."""

import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from functools import lru_cache
from datetime import datetime, timedelta


class ScanCache:
    """Cache for scan results to avoid duplicate analysis."""

    def __init__(self, ttl_minutes: int = 60):
        """Initialize scan cache."""
        self.cache: Dict[str, tuple] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    def get_cache_key(self, repo_name: str, commit_hash: str) -> str:
        """Generate cache key for a scan."""
        key = f"{repo_name}:{commit_hash}"
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, repo_name: str, commit_hash: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        key = self.get_cache_key(repo_name, commit_hash)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.utcnow() - timestamp < self.ttl:
                return result
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None

    def set(self, repo_name: str, commit_hash: str, result: Any) -> None:
        """Cache a scan result."""
        key = self.get_cache_key(repo_name, commit_hash)
        self.cache[key] = (result, datetime.utcnow())

    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()

    def get_size(self) -> int:
        """Get cache size in bytes (approximate)."""
        return len(str(self.cache).encode())


class AsyncAnalyzer:
    """Asynchronous code analyzer for large PRs."""

    def __init__(self, max_workers: int = 4):
        """Initialize async analyzer."""
        self.max_workers = max_workers

    async def analyze_files_async(
        self,
        files: Dict[str, str],
        analyzer_func,
        file_path_prefix: str = ""
    ) -> List[Any]:
        """
        Analyze multiple files asynchronously.
        Returns list of analysis results.
        """
        tasks = []

        for file_path, content in files.items():
            task = self._analyze_file_async(
                file_path,
                content,
                analyzer_func,
                file_path_prefix
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]

        return valid_results

    async def _analyze_file_async(
        self,
        file_path: str,
        content: str,
        analyzer_func,
        file_path_prefix: str
    ) -> Any:
        """Analyze a single file asynchronously."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            analyzer_func,
            content,
            file_path_prefix + file_path
        )
        return result


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True

        return False

    def get_reset_time(self, identifier: str) -> Optional[datetime]:
        """Get when rate limit will reset for identifier."""
        if identifier not in self.requests or not self.requests[identifier]:
            return None

        oldest_request = min(self.requests[identifier])
        return oldest_request + timedelta(seconds=self.window_seconds)

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        if identifier not in self.requests:
            return self.max_requests

        valid_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        return max(0, self.max_requests - len(valid_requests))


class BackgroundJobQueue:
    """Queue for background analysis jobs."""

    def __init__(self):
        """Initialize job queue."""
        self.queue: List[Dict[str, Any]] = []
        self.processing: Dict[str, bool] = {}
        self.results: Dict[str, Any] = {}

    def enqueue(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Add job to queue."""
        self.queue.append({
            "id": job_id,
            "data": job_data,
            "status": "queued",
            "created_at": datetime.utcnow(),
        })

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Remove and return next job from queue."""
        if self.queue:
            return self.queue.pop(0)
        return None

    def mark_processing(self, job_id: str) -> None:
        """Mark job as processing."""
        self.processing[job_id] = True

    def mark_complete(self, job_id: str, result: Any) -> None:
        """Mark job as complete and store result."""
        self.processing[job_id] = False
        self.results[job_id] = result

    def get_result(self, job_id: str) -> Optional[Any]:
        """Get result of completed job."""
        return self.results.get(job_id)

    def is_processing(self, job_id: str) -> bool:
        """Check if job is currently processing."""
        return self.processing.get(job_id, False)

    def queue_size(self) -> int:
        """Get queue size."""
        return len(self.queue)


class AnalysisOptimizer:
    """Optimize analysis for large PRs."""

    @staticmethod
    def prioritize_files(files: Dict[str, str]) -> List[tuple]:
        """
        Prioritize files for analysis.
        Returns list of (file_path, content) sorted by priority.
        """
        priority_scores = []

        for file_path, content in files.items():
            # Calculate priority based on multiple factors
            score = 0

            # Higher priority for security-sensitive files
            security_files = [".py", ".js", ".ts", ".java", ".go", ".rb"]
            if any(file_path.endswith(ext) for ext in security_files):
                score += 100

            # Higher priority for smaller files (analyze first)
            content_size = len(content)
            if content_size < 1000:
                score += 50
            elif content_size > 10000:
                score -= 30

            # Lower priority for test files
            if "test" in file_path.lower():
                score -= 20

            priority_scores.append((file_path, content, score))

        # Sort by score (descending)
        priority_scores.sort(key=lambda x: x[2], reverse=True)

        return [(path, content) for path, content, _ in priority_scores]

    @staticmethod
    def chunk_large_pr(files: Dict[str, str], chunk_size: int = 10) -> List[Dict[str, str]]:
        """
        Chunk large PR into smaller batches for parallel processing.
        """
        chunks = []
        current_chunk = {}
        current_size = 0

        for file_path, content in files.items():
            current_chunk[file_path] = content
            current_size += len(content)

            if current_size > chunk_size * 1000:  # chunk_size in KB
                chunks.append(current_chunk)
                current_chunk = {}
                current_size = 0

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
