from collections import Counter


class DatasetService:
    def get_dataset_report(self, samples: list[dict]) -> dict:
        total_samples = len(samples)
        class_distribution = self.compute_class_distribution(samples)
        empty_images = sum(1 for item in samples if not item.get("bboxes", []))
        empty_image_ratio = (empty_images / total_samples) if total_samples else 0.0

        return {
            "total_samples": total_samples,
            "class_distribution": class_distribution,
            "empty_image_ratio": empty_image_ratio,
            "bbox_size_distribution": self.compute_bbox_size_distribution(samples),
            "scene_coverage": {
                "single": self.compute_scene_coverage(samples, dimensions=["weather"]),
                "combination": self.compute_scene_coverage(samples, dimensions=["time_of_day", "weather"]),
            },
        }

    @staticmethod
    def compute_class_distribution(samples: list[dict]) -> dict[str, int]:
        distribution = Counter()
        for item in samples:
            for class_name in item.get("classes", []):
                distribution[class_name] += 1
        return dict(distribution)

    @staticmethod
    def compute_bbox_size_distribution(samples: list[dict]) -> dict[str, int]:
        buckets = {"small": 0, "medium": 0, "large": 0}
        for item in samples:
            for bbox in item.get("bboxes", []):
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                area = width * height
                if area < 1024:
                    buckets["small"] += 1
                elif area < 10000:
                    buckets["medium"] += 1
                else:
                    buckets["large"] += 1
        return buckets

    @staticmethod
    def compute_scene_coverage(samples: list[dict], *, dimensions: list[str]) -> list[dict]:
        counter = Counter()
        for item in samples:
            scene = item.get("scene", {})
            key = "+".join(str(scene.get(dimension, "unknown")) for dimension in dimensions)
            counter[key] += 1

        total = sum(counter.values())
        if total == 0:
            return []

        output = []
        for key in sorted(counter):
            count = counter[key]
            output.append({"dimension_key": key, "count": count, "ratio": count / total})
        return output
