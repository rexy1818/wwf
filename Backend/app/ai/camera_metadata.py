import easyocr
import re


class CameraMetadataExtractor:

    def __init__(self):

        self.reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

    def extract(self, image_path):

        try:

            results = self.reader.readtext(
                image_path
            )

            text = " ".join(
                [
                    item[1]
                    for item in results
                ]
            )

            camera_id = None
            date = None
            time = None
            temperature = None

            date_match = re.search(
                r"\d{2}-\d{2}-\d{4}",
                text
            )

            time_match = re.search(
                r"\d{2}:\d{2}:\d{2}",
                text
            )

            temp_match = re.search(
                r"(\d+)\s*°?C",
                text,
                re.IGNORECASE
            )

            camera_match = re.search(
                r"[A-Z]{2,}\d+[A-Z]?",
                text
            )

            if date_match:
                date = date_match.group()

            if time_match:
                time = time_match.group()

            if temp_match:
                temperature = int(
                    temp_match.group(1)
                )

            if camera_match:
                camera_id = (
                    camera_match.group()
                )

            return {
                "camera_id": camera_id,
                "date": date,
                "time": time,
                "temperature_c": temperature
            }

        except Exception as e:

            return {
                "camera_id": None,
                "date": None,
                "time": None,
                "temperature_c": None,
                "error": str(e)
            }