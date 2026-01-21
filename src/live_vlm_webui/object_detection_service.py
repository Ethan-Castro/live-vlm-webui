# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Object Detection Service
Handles real-time object detection using YOLO models.

This module requires ultralytics to be installed. On resource-constrained
devices like Raspberry Pi, this dependency is optional.
"""

import asyncio
import logging
import time
import numpy as np
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import YOLO - it's optional
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO = None
    YOLO_AVAILABLE = False
    logger.warning("ultralytics not installed - YOLO object detection unavailable")
    logger.info("Install with: pip install ultralytics")


class ObjectDetectionService:
    """Service for detecting objects in frames using YOLO"""

    def __init__(self, model_path: str = "yolo26n-seg.pt", confidence: float = 0.25):
        """
        Initialize YOLO service

        Args:
            model_path: Path to YOLO model (e.g., "yolov8n.pt")
            confidence: Confidence threshold for detection
        
        Raises:
            ImportError: If ultralytics is not installed
        """
        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics is required for object detection. "
                "Install with: pip install ultralytics"
            )
        
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        self.is_initialized = False
        self.current_detections = []
        self._processing_lock = asyncio.Lock()
        
        # Metrics tracking
        self.last_inference_time = 0.0
        self.total_inferences = 0
        self.total_inference_time = 0.0

    def initialize(self):
        """Load the YOLO model (can be slow, so call outside main loop)"""
        if self.is_initialized:
            return
        
        if not YOLO_AVAILABLE:
            logger.error("Cannot initialize YOLO - ultralytics not installed")
            return
            
        try:
            logger.info(f"Loading Ultralytics YOLO26 model: {self.model_path}...")
            self.model = YOLO(self.model_path)
            # YOLO26 is NMS-free and optimized for edge/CPU
            # Warm up the model
            self.model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
            self.is_initialized = True
            logger.info("YOLO26 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO26 model: {e}")
            raise

    async def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection on a single frame

        Args:
            image: BGR numpy array

        Returns:
            List of detections: [{"box": [x1, y1, x2, y2], "label": str, "conf": float}]
        """
        if not self.is_initialized:
            self.initialize()

        try:
            start_time = time.perf_counter()
            
            # Run inference in a thread to avoid blocking the event loop
            results = await asyncio.to_thread(
                self.model, image, conf=self.confidence, verbose=False
            )
            
            detections = []
            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes
                masks = getattr(result, 'masks', None)
                
                for i in range(len(boxes)):
                    box = boxes[i]
                    # Get box coordinates in [x1, y1, x2, y2] format
                    coords = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = self.model.names[cls]
                    
                    det = {
                        "box": [round(c, 1) for c in coords],
                        "label": label,
                        "class_id": cls,
                        "conf": round(conf, 2)
                    }

                    # Add segmentation mask if available
                    if masks is not None:
                        # xy is a list of segments (polygons)
                        segments = masks.xy[i]
                        if segments is not None and len(segments) > 0:
                            det["mask"] = segments.tolist()
                    
                    detections.append(det)

            end_time = time.perf_counter()
            inference_time = end_time - start_time
            
            # Update metrics
            self.last_inference_time = inference_time
            self.total_inferences += 1
            self.total_inference_time += inference_time
            
            return detections

        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            return []

    async def process_frame(self, image: np.ndarray) -> None:
        """
        Process a frame asynchronously. Updates self.current_detections when done.
        """
        if self._processing_lock.locked():
            return

        async with self._processing_lock:
            detections = await self.detect(image)
            self.current_detections = detections

    def get_current_detections(self) -> List[Dict[str, Any]]:
        """Get the most recent detection results"""
        return self.current_detections

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_latency = (
            self.total_inference_time / self.total_inferences if self.total_inferences > 0 else 0.0
        )
        return {
            "last_latency_ms": self.last_inference_time * 1000,
            "avg_latency_ms": avg_latency * 1000,
            "total_detections": self.total_inferences
        }
