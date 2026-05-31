from PIL import Image
from speciesnet import SpeciesNetClassifier


class SpeciesClassifier:

    def __init__(self):

        self.classifier = SpeciesNetClassifier(
            model_name="kaggle:google/speciesnet/pyTorch/v4.0.2b/1"
        )

    def classify(self, image_path):

        try:

            img = Image.open(image_path)

            processed = self.classifier.preprocess(
                img
            )

            result = self.classifier.predict(
                image_path,
                processed
            )

            classes = result[
                "classifications"
            ]["classes"]

            scores = result[
                "classifications"
            ]["scores"]

            best_class = classes[0]
            best_score = scores[0]

            taxonomy = best_class.split(";")

            scientific_name = (
                f"{taxonomy[4]} {taxonomy[5]}"
            )

            common_name = taxonomy[6]

            return {
                "species": common_name,
                "scientific_name": scientific_name,
                "confidence": float(best_score)
            }

        except Exception as e:

            return {
                "species": "unknown",
                "scientific_name": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }