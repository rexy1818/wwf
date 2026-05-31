import os

from app.ai.pipeline import VideoPipeline


class VideoService:

    def __init__(self):
        self.pipeline = VideoPipeline()

    def process_video(self, video_path):

        if not os.path.exists(video_path):
            raise FileNotFoundError(
                f"Video no encontrado: {video_path}"
            )

        return self.pipeline.process_video(
            video_path
        )

    def process_all_videos(self):

        uploads_folder = "storage/uploads"

        if not os.path.exists(
            uploads_folder
        ):
            return []

        results = []

        for file_name in os.listdir(
            uploads_folder
        ):

            if not file_name.lower().endswith(
                (
                    ".mp4",
                    ".avi",
                    ".mov",
                    ".mkv"
                )
            ):
                continue

            video_path = os.path.join(
                uploads_folder,
                file_name
            )

            result = self.process_video(
                video_path
            )

            best_detection = result.get(
                "best_detection"
            )

            results.append({

                "video":
                file_name,

                "species":
                best_detection.get(
                    "species",
                    "unknown"
                )
                if best_detection
                else "unknown",

                "scientific_name":
                best_detection.get(
                    "scientific_name",
                    ""
                )
                if best_detection
                else "",

                "confidence":
                best_detection.get(
                    "species_confidence",
                    0
                )
                if best_detection
                else 0,

                "image":
                result.get(
                    "best_image"
                )

            })

        return results