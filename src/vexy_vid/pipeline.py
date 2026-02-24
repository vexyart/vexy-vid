"""High-performance frame buffer pool and video processing pipeline."""

import queue
import threading
from typing import Any, Callable, List, Optional, Tuple

import numpy as np
from loguru import logger

from vexy_vid.constants import (
    BUFFER_POOL_SIZE,
    MAX_WORKERS,
    QUEUE_SIZE,
)
from vexy_vid.frames import extract_frame_fast


class FrameBufferPool:
    """
    High-performance frame buffer pool for reduced memory allocation overhead.
    Pre-allocates buffers to avoid repeated malloc/free cycles during processing.
    """

    def __init__(
        self,
        pool_size: int = BUFFER_POOL_SIZE,
        frame_shape: Tuple[int, int, int] = (2160, 3840, 3),
    ):
        """
        Initialize buffer pool with pre-allocated frame buffers.

        Args:
            pool_size: Number of buffers to pre-allocate
            frame_shape: Default frame shape (height, width, channels) for 4K
        """
        self.pool = queue.Queue(maxsize=pool_size)
        self.frame_shape = frame_shape
        self.pool_size = pool_size

        # Pre-allocate buffers
        for _ in range(pool_size):
            buffer = np.empty(frame_shape, dtype=np.uint8)
            self.pool.put(buffer)

        logger.debug(f"Initialized buffer pool with {pool_size} buffers of shape {frame_shape}")

    def get_buffer(self, shape: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        """
        Get a buffer from the pool or create new one if pool is empty.

        Args:
            shape: Required buffer shape, uses default if None

        Returns:
            Pre-allocated or new numpy array buffer
        """
        target_shape = shape or self.frame_shape

        try:
            buffer = self.pool.get_nowait()
            # Reshape if needed (cheap operation, just changes metadata)
            if buffer.shape != target_shape:
                return np.empty(target_shape, dtype=np.uint8)
            return buffer
        except queue.Empty:
            # Pool exhausted, create new buffer
            return np.empty(target_shape, dtype=np.uint8)

    def return_buffer(self, buffer: np.ndarray) -> None:
        """
        Return a buffer to the pool for reuse.

        Args:
            buffer: Buffer to return to pool
        """
        try:
            self.pool.put_nowait(buffer)
        except queue.Full:
            # Pool is full, let buffer be garbage collected
            pass


# Global instances for reuse
_buffer_pool = None


def get_buffer_pool(frame_shape: Optional[Tuple[int, int, int]] = None) -> FrameBufferPool:
    """Get or create global buffer pool instance."""
    global _buffer_pool
    if _buffer_pool is None:
        shape = frame_shape or (2160, 3840, 3)  # Default 4K shape
        _buffer_pool = FrameBufferPool(frame_shape=shape)
    return _buffer_pool


class VideoProcessingPipeline:
    """
    High-performance producer-consumer pipeline for video frame processing.
    Implements stage-based architecture with optimal queue management.
    """

    def __init__(self, max_workers: int = MAX_WORKERS, queue_size: int = QUEUE_SIZE):
        """
        Initialize the processing pipeline.

        Args:
            max_workers: Maximum number of worker threads/processes
            queue_size: Size of processing queues
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.buffer_pool = get_buffer_pool()

        # Processing queues
        self.input_queue = queue.Queue(maxsize=queue_size)
        self.output_queue = queue.Queue(maxsize=queue_size)

        # Control flags
        self.stop_processing = threading.Event()

        logger.debug(f"Initialized pipeline with {max_workers} workers, queue size {queue_size}")

    def frame_reader_worker(self, video_path: str, frame_indices: List[int]) -> None:
        """
        Producer worker that reads frames and feeds them to processing queue.

        Args:
            video_path: Path to input video
            frame_indices: List of frame indices to process
        """
        try:
            frames_read = 0
            for frame_idx in frame_indices:
                if self.stop_processing.is_set():
                    break

                # Extract frame using optimized PyAV method
                frame = extract_frame_fast(video_path, frame_idx)

                if frame is not None:
                    # Put frame into queue with index for ordering
                    self.input_queue.put((frame_idx, frame))
                    frames_read += 1
                else:
                    logger.debug(f"Failed to read frame {frame_idx}")

                # Backpressure control - avoid overwhelming the queue
                if self.input_queue.qsize() > self.queue_size * 0.8:
                    threading.Event().wait(0.001)  # Small delay

            logger.debug(f"Frame reader finished: {frames_read} frames read")

        except Exception as e:
            logger.error(f"Frame reader error: {e}")
        finally:
            # Signal end of input
            self.input_queue.put(None)

    def frame_processor_worker(self, processor_func: Callable, processor_args: tuple = ()) -> None:
        """
        Consumer worker that processes frames from the input queue.

        Args:
            processor_func: Function to process each frame
            processor_args: Additional arguments for processor function
        """
        try:
            frames_processed = 0

            while not self.stop_processing.is_set():
                try:
                    # Get frame from input queue
                    item = self.input_queue.get(timeout=1.0)

                    if item is None:
                        # End of input signal
                        break

                    frame_idx, frame = item

                    # Process frame
                    try:
                        result = processor_func(frame, *processor_args)

                        # Put result into output queue
                        self.output_queue.put((frame_idx, result))
                        frames_processed += 1

                    except Exception as proc_error:
                        logger.debug(f"Frame {frame_idx} processing failed: {proc_error}")
                        # Put None result to maintain order
                        self.output_queue.put((frame_idx, None))

                    finally:
                        # Return frame buffer to pool
                        self.buffer_pool.return_buffer(frame)

                except queue.Empty:
                    continue

            logger.debug(f"Frame processor finished: {frames_processed} frames processed")

        except Exception as e:
            logger.error(f"Frame processor error: {e}")
        finally:
            # Signal end of processing
            self.output_queue.put(None)

    def process_frames_parallel(
        self,
        video_path: str,
        frame_indices: List[int],
        processor_func: Callable,
        processor_args: tuple = (),
        progress_callback: Optional[Callable] = None,
    ) -> List[Any]:
        """
        Process frames using producer-consumer pipeline.

        Args:
            video_path: Path to input video
            frame_indices: List of frame indices to process
            processor_func: Function to process each frame
            processor_args: Additional arguments for processor function
            progress_callback: Optional callback for progress updates

        Returns:
            List of processing results in original order
        """
        results = {}
        processed_count = 0
        total_frames = len(frame_indices)

        try:
            # Start frame reader thread
            reader_thread = threading.Thread(
                target=self.frame_reader_worker, args=(video_path, frame_indices), daemon=True
            )
            reader_thread.start()

            # Start processor workers
            processor_threads = []
            for _ in range(min(self.max_workers, 4)):
                worker_thread = threading.Thread(
                    target=self.frame_processor_worker,
                    args=(processor_func, processor_args),
                    daemon=True,
                )
                worker_thread.start()
                processor_threads.append(worker_thread)

            # Collect results
            active_processors = len(processor_threads)

            while active_processors > 0:
                try:
                    item = self.output_queue.get(timeout=2.0)

                    if item is None:
                        active_processors -= 1
                        continue

                    frame_idx, result = item
                    results[frame_idx] = result
                    processed_count += 1

                    # Progress callback
                    if progress_callback and processed_count % 5 == 0:
                        progress_callback(processed_count, total_frames)

                except queue.Empty:
                    # Check if we should timeout
                    if not reader_thread.is_alive() and all(
                        not t.is_alive() for t in processor_threads
                    ):
                        break

            # Wait for threads to complete
            reader_thread.join(timeout=1.0)
            for thread in processor_threads:
                thread.join(timeout=1.0)

            # Return results in original order
            ordered_results = []
            for idx in frame_indices:
                ordered_results.append(results.get(idx))

            logger.debug(f"Pipeline processed {processed_count}/{total_frames} frames successfully")
            return ordered_results

        except Exception as e:
            logger.error(f"Pipeline processing error: {e}")
            self.stop_processing.set()
            raise
        finally:
            # Clean up
            self.stop_processing.clear()


# Global pipeline instance for reuse
_processing_pipeline = None


def get_processing_pipeline() -> VideoProcessingPipeline:
    """Get or create global processing pipeline instance."""
    global _processing_pipeline
    if _processing_pipeline is None:
        _processing_pipeline = VideoProcessingPipeline()
    return _processing_pipeline
