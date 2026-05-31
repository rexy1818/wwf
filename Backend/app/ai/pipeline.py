import os
import cv2
import json
import glob

from app.ai.detector import AnimalDetector
from app.ai.classifier import SpeciesClassifier
from app.ai.camera_metadata import (
    CameraMetadataExtractor
)


class VideoPipeline:

    def __init__(self):

        self.detector = AnimalDetector()

        self.classifier = SpeciesClassifier()

        self.metadata_extractor = (
            CameraMetadataExtractor()
        )

    def process_video(
        self,
        video_path
    ):

        video_name = os.path.splitext(
            os.path.basename(video_path)
        )[0]

        frames_folder = (
            f"storage/frames/{video_name}"
        )

        os.makedirs(
            frames_folder,
            exist_ok=True
        )

        cap = cv2.VideoCapture(
            video_path
        )

        frame_count = 0

        results = []

        best_detection = None

        best_frame_path = None

        while True:

            success, frame = cap.read()

            if not success:
                break

            # Analizar 1 frame por segundo
            if frame_count % 30 == 0:

                frame_name = (
                    f"frame_{frame_count}.jpg"
                )

                frame_path = os.path.join(
                    frames_folder,
                    frame_name
                )

                cv2.imwrite(
                    frame_path,
                    frame
                )

                metadata = (
                    self.metadata_extractor.extract(
                        frame_path
                    )
                )

                detections = (
                    self.detector.detect(
                        frame_path
                    )
                )

                for detection in detections:

                    if (
                        best_detection is None
                        or
                        detection[
                            "species_confidence"
                        ]
                        >
                        best_detection[
                            "species_confidence"
                        ]
                    ):

                        best_detection = {
                            **detection,
                            "frame": frame_name,
                            "camera_metadata":
                            metadata
                        }

                        best_frame_path = (
                            frame_path
                        )

                results.append({

                    "frame":
                    frame_name,

                    "camera_metadata":
                    metadata,

                    "detections":
                    detections

                })

            frame_count += 1

        cap.release()

        os.makedirs(
            "storage/best",
            exist_ok=True
        )

        best_image_path = None

        if (
            best_detection is not None
            and
            best_frame_path is not None
        ):

            image = cv2.imread(
                best_frame_path
            )

            x1, y1, x2, y2 = (
                best_detection["bbox"]
            )

            cv2.rectangle(
                image,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )

            label = (
                f"{best_detection['species']} "
                f"{best_detection['species_confidence']:.2f}"
            )

            cv2.putText(
                image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            best_image_path = (
                f"storage/best/{video_name}.jpg"
            )

            cv2.imwrite(
                best_image_path,
                image
            )

        final_result = {

            "video":
            video_name,

            "best_detection":
            best_detection,

            "best_image":
            best_image_path,

            "frames":
            results

        }

        os.makedirs(
            "storage/results",
            exist_ok=True
        )

        json_path = (
            f"storage/results/{video_name}.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                final_result,
                file,
                indent=4,
                ensure_ascii=False
            )

        best_crop = None

        if best_detection:

            best_crop = (
                best_detection[
                    "crop_path"
                ]
            )

        for crop_file in glob.glob(
            "storage/crops/*.jpg"
        ):

            if crop_file != best_crop:

                try:

                    os.remove(
                        crop_file
                    )

                except Exception:
                    pass

        return final_result