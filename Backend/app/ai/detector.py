from ultralytics import YOLO
from app.ai.classifier import SpeciesClassifier

import cv2
import os


class AnimalDetector:

    def __init__(self):

        self.model = YOLO(
            "yolo11n.pt"
        )

        self.classifier = (
            SpeciesClassifier()
        )

        self.valid_classes = [
            "person",
            "dog",
            "cat",
            "bear",
            "bird",
            "horse",
            "cow",
            "sheep",
            "elephant",
            "zebra",
            "giraffe"
        ]

        os.makedirs(
            "storage/crops",
            exist_ok=True
        )

    def detect(self, image_path):

        image = cv2.imread(
            image_path
        )

        if image is None:
            return []

        results = self.model(
            image_path
        )

        detections = []

        frame_name = os.path.splitext(
            os.path.basename(image_path)
        )[0]

        crop_index = 0

        for result in results:

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                class_name = (
                    result.names[
                        class_id
                    ]
                )

                if class_name not in self.valid_classes:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                if (
                    x2 <= x1
                    or
                    y2 <= y1
                ):
                    continue

                crop = image[
                    y1:y2,
                    x1:x2
                ]

                if crop.size == 0:
                    continue

                crop_name = (
                    f"{frame_name}_crop_{crop_index}.jpg"
                )

                crop_path = os.path.join(
                    "storage/crops",
                    crop_name
                )

                cv2.imwrite(
                    crop_path,
                    crop
                )

                species_result = (
                    self.classifier.classify(
                        crop_path
                    )
                )

                confidence = (
                    species_result[
                        "confidence"
                    ]
                )

                species_name = (
                    species_result[
                        "species"
                    ]
                )

                if confidence < 0.60:

                    species_name = (
                        "review_required"
                    )

                detections.append({

                    "species":
                        species_name,

                    "scientific_name":
                        species_result[
                            "scientific_name"
                        ],

                    "species_confidence":
                        confidence,

                    "detected_class":
                        class_name,

                    "detection_confidence":
                        float(
                            box.conf[0]
                        ),

                    "bbox": [
                        x1,
                        y1,
                        x2,
                        y2
                    ],

                    "crop_path":
                        crop_path
                })

                crop_index += 1

        return detections