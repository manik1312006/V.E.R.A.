"""
tools/screen_vision.py — On-demand screen capture tool for V.E.R.A.

Provides a lightweight wrapper around mss for grabbing screen frames,
used by the Gemini Live provider when it needs to see the screen.
"""

import base64
import io
from typing import Optional
from utils.logger import get_logger

logger = get_logger("vera.screen_vision")


class ScreenVision:
    """On-demand screen capture tool powered by mss."""

    def capture_frame(
        self,
        monitor_index: int = 1,
        max_width: int = 1280,
        jpeg_quality: int = 70,
    ) -> Optional[bytes]:
        """
        Captures the screen and returns JPEG bytes.

        Args:
            monitor_index: Which monitor to capture (1 = primary).
            max_width: Maximum width to resize to (preserves aspect ratio).
            jpeg_quality: JPEG compression quality (1–95).

        Returns:
            Raw JPEG bytes, or None on failure.
        """
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitor = sct.monitors[monitor_index]
                shot = sct.grab(monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

                if img.width > max_width:
                    ratio = max_width / img.width
                    img = img.resize(
                        (max_width, int(img.height * ratio)),
                        Image.LANCZOS,
                    )

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=jpeg_quality)
                logger.debug(f"Screen captured: {img.width}x{img.height}px")
                return buf.getvalue()

        except ImportError:
            logger.error("mss or Pillow not installed. Run: pip install mss pillow")
            return None
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None

    def capture_as_base64(self, **kwargs) -> Optional[str]:
        """
        Captures the screen and returns a base64-encoded JPEG string.

        Returns:
            Base64 string, or None on failure.
        """
        raw = self.capture_frame(**kwargs)
        if raw is None:
            return None
        return base64.b64encode(raw).decode("utf-8")

    def capture_as_data_url(self, **kwargs) -> Optional[str]:
        """
        Captures the screen and returns a data URL (usable in img tags / APIs).

        Returns:
            'data:image/jpeg;base64,...' string, or None on failure.
        """
        b64 = self.capture_as_base64(**kwargs)
        if b64 is None:
            return None
        return f"data:image/jpeg;base64,{b64}"

    def save_screenshot(self, path: str = "screenshot.png") -> bool:
        """
        Saves a screenshot to disk.

        Args:
            path: File path to save to.

        Returns:
            True if saved successfully.
        """
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                shot = sct.grab(monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                img.save(path)
                logger.info(f"Screenshot saved to {path}")
                return True
        except Exception as e:
            logger.error(f"Screenshot save failed: {e}")
            return False
