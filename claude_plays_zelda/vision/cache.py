"""Vision processing cache for optimization."""

import time
import hashlib
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass
from collections import OrderedDict
import numpy as np
from loguru import logger


@dataclass
class CacheEntry:
    """Cache entry with data and metadata."""

    value: Any
    timestamp: float
    hit_count: int = 0
    compute_time: float = 0.0


class VisionCache:
    """
    LRU cache for vision processing results with TTL support.

    This cache helps optimize repeated vision operations by storing
    results and avoiding redundant computation when game state is stable.
    """

    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: float = 1.0,
        enable_stats: bool = True,
    ):
        """
        Initialize vision cache.

        Args:
            max_size: Maximum number of cached entries
            ttl_seconds: Time-to-live for cache entries in seconds
            enable_stats: Whether to track cache statistics
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_stats = enable_stats

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.info(
            f"VisionCache initialized: max_size={max_size}, "
            f"ttl={ttl_seconds}s, stats={'enabled' if enable_stats else 'disabled'}"
        )

    def _compute_key(self, image: np.ndarray, operation: str, params: tuple = ()) -> str:
        """
        Compute cache key from image and operation parameters.

        Args:
            image: Input image
            operation: Operation name
            params: Additional parameters

        Returns:
            Cache key string
        """
        # Use image hash + operation + params as key
        image_hash = hashlib.md5(image.tobytes(), usedforsecurity=False).hexdigest()[:16]
        params_str = "_".join(str(p) for p in params)
        return f"{operation}_{image_hash}_{params_str}"

    def get(self, image: np.ndarray, operation: str, params: tuple = ()) -> Optional[Any]:
        """
        Get cached result if available and valid.

        Args:
            image: Input image
            operation: Operation name
            params: Additional parameters

        Returns:
            Cached value or None if not found/expired
        """
        key = self._compute_key(image, operation, params)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Check if entry has expired
        age = time.time() - entry.timestamp
        if age > self.ttl_seconds:
            # Entry expired, remove it
            del self._cache[key]
            self._misses += 1
            return None

        # Cache hit! Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hit_count += 1
        self._hits += 1

        logger.debug(f"Cache HIT: {operation} (age={age:.2f}s, hits={entry.hit_count})")
        return entry.value

    def put(
        self,
        image: np.ndarray,
        operation: str,
        value: Any,
        params: tuple = (),
        compute_time: float = 0.0,
    ):
        """
        Store result in cache.

        Args:
            image: Input image
            operation: Operation name
            value: Result to cache
            params: Additional parameters
            compute_time: Time taken to compute result
        """
        key = self._compute_key(image, operation, params)

        # Check if we need to evict
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Remove oldest entry (first item)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._evictions += 1
            logger.debug(f"Cache eviction: {oldest_key}")

        # Store new entry
        self._cache[key] = CacheEntry(value=value, timestamp=time.time(), compute_time=compute_time)

        # Move to end (most recently used)
        self._cache.move_to_end(key)

        logger.debug(f"Cache PUT: {operation} (compute_time={compute_time:.3f}s)")

    def cached_operation(
        self, image: np.ndarray, operation: str, func: Callable, params: tuple = ()
    ) -> Any:
        """
        Execute operation with caching.

        Args:
            image: Input image
            operation: Operation name
            func: Function to execute if cache miss
            params: Additional parameters

        Returns:
            Operation result (cached or computed)
        """
        # Try to get from cache
        result = self.get(image, operation, params)
        if result is not None:
            return result

        # Cache miss - compute result
        start_time = time.time()
        result = func()
        compute_time = time.time() - start_time

        # Store in cache
        self.put(image, operation, result, params, compute_time)

        return result

    def clear(self, operation: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            operation: If specified, only clear entries for this operation.
                      If None, clear all entries.
        """
        if operation is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries removed")
        else:
            # Remove entries matching operation
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{operation}_")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cache cleared for '{operation}': {len(keys_to_remove)} entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }

    def log_stats(self):
        """Log cache statistics."""
        if not self.enable_stats:
            return

        stats = self.get_stats()
        logger.info(
            f"Cache Stats: "
            f"size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate']:.1f}%, "
            f"hits={stats['hits']}, "
            f"misses={stats['misses']}, "
            f"evictions={stats['evictions']}"
        )

    def reset_stats(self):
        """Reset cache statistics."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        logger.info("Cache statistics reset")


class ImageComparator:
    """Utility to compare images for similarity to optimize caching."""

    @staticmethod
    def compute_hash(image: np.ndarray) -> str:
        """
        Compute a cryptographic hash of the image's raw byte content.

        Note: This is not a perceptual hash. Any minor change to the image
        will result in a completely different hash.

        Args:
            image: Input image

        Returns:
            MD5 hash string
        """
        return hashlib.md5(image.tobytes(), usedforsecurity=False).hexdigest()

    @staticmethod
    def are_similar(image1: np.ndarray, image2: np.ndarray, threshold: float = 0.95) -> bool:
        """
        Check if two images are similar.

        Args:
            image1: First image
            image2: Second image
            threshold: Similarity threshold (0-1)

        Returns:
            True if images are similar
        """
        # Quick shape check
        if image1.shape != image2.shape:
            return False

        # Compute pixel-wise difference
        diff = np.abs(image1.astype(float) - image2.astype(float))
        similarity = 1.0 - (np.mean(diff) / 255.0)

        return similarity >= threshold

    @staticmethod
    def has_significant_change(
        image1: np.ndarray, image2: np.ndarray, threshold: float = 0.05
    ) -> bool:
        """
        Check if there's significant change between images.

        Args:
            image1: Previous image
            image2: Current image
            threshold: Change threshold (0-1)

        Returns:
            True if significant change detected
        """
        return not ImageComparator.are_similar(image1, image2, threshold=1.0 - threshold)


class AdaptiveVisionProcessor:
    """
    Vision processor with adaptive frame rate based on scene changes.

    This processor automatically reduces processing rate when the scene
    is stable, improving performance without sacrificing responsiveness.
    """

    def __init__(
        self,
        min_interval: float = 0.1,
        max_interval: float = 1.0,
        change_threshold: float = 0.05,
    ):
        """
        Initialize adaptive processor.

        Args:
            min_interval: Minimum interval between processing (seconds)
            max_interval: Maximum interval when scene is stable (seconds)
            change_threshold: Threshold for detecting scene changes
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.change_threshold = change_threshold

        self._last_image: Optional[np.ndarray] = None
        self._last_process_time = 0.0
        self._current_interval = min_interval
        self._stable_frames = 0

        logger.info(
            f"AdaptiveVisionProcessor initialized: " f"interval={min_interval}-{max_interval}s"
        )

    def should_process(self, image: np.ndarray) -> bool:
        """
        Determine if image should be processed.

        Args:
            image: Current image

        Returns:
            True if processing should occur
        """
        current_time = time.time()
        elapsed = current_time - self._last_process_time

        # Check if minimum interval has passed
        if elapsed < self._current_interval:
            return False

        # If this is first frame, process it
        if self._last_image is None:
            self._last_image = image.copy()
            self._last_process_time = current_time
            return True

        # Check for significant changes
        has_change = ImageComparator.has_significant_change(
            self._last_image, image, threshold=self.change_threshold
        )

        if has_change:
            # Scene changed - reset to minimum interval
            self._current_interval = self.min_interval
            self._stable_frames = 0
            logger.debug("Scene change detected, increasing processing rate")
        else:
            # Scene stable - gradually increase interval
            self._stable_frames += 1
            if self._stable_frames > 10:
                self._current_interval = min(self._current_interval * 1.2, self.max_interval)
                logger.debug(
                    f"Scene stable, reducing processing rate "
                    f"(interval={self._current_interval:.2f}s)"
                )

        self._last_image = image.copy()
        self._last_process_time = current_time
        return True

    def get_current_interval(self) -> float:
        """Get current processing interval."""
        return self._current_interval

    def reset(self):
        """Reset processor state."""
        self._last_image = None
        self._last_process_time = 0.0
        self._current_interval = self.min_interval
        self._stable_frames = 0
