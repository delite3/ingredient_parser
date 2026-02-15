import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import cv2
import easyocr
import Levenshtein
import numpy as np

from Analyser import EWGSkindeepAPI


STOP_SECTION_KEYWORDS = {
    "directions",
    "warning",
    "warnings",
    "caution",
    "how to use",
    "storage",
    "manufactured",
    "distributed",
    "made in",
    "best before",
    "expiration",
    "exp",
    "lot",
    "barcode",
}


@dataclass
class OCRLine:
    text: str
    conf: float
    box: Sequence[Sequence[float]]

    @property
    def x_min(self) -> float:
        return float(min(point[0] for point in self.box))

    @property
    def x_max(self) -> float:
        return float(max(point[0] for point in self.box))

    @property
    def y_min(self) -> float:
        return float(min(point[1] for point in self.box))

    @property
    def y_max(self) -> float:
        return float(max(point[1] for point in self.box))

    @property
    def y_center(self) -> float:
        return (self.y_min + self.y_max) / 2.0


class RobustIngredientOCR:
    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False):
        self.reader = easyocr.Reader(languages or ["en"], gpu=use_gpu)

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text.strip())
        return text

    @staticmethod
    def _is_ingredient_header(text: str) -> bool:
        compact = re.sub(r"[^a-z]", "", text.lower())
        if not compact:
            return False
        if "ingredient" in compact or "ingredients" in compact:
            return True
        return Levenshtein.ratio("ingredients", compact[:11]) >= 0.73

    @staticmethod
    def _is_section_stop(text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in STOP_SECTION_KEYWORDS)

    @staticmethod
    def _iou(a: OCRLine, b: OCRLine) -> float:
        x_left = max(a.x_min, b.x_min)
        y_top = max(a.y_min, b.y_min)
        x_right = min(a.x_max, b.x_max)
        y_bottom = min(a.y_max, b.y_max)
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0

        intersection = (x_right - x_left) * (y_bottom - y_top)
        area_a = max((a.x_max - a.x_min) * (a.y_max - a.y_min), 1.0)
        area_b = max((b.x_max - b.x_min) * (b.y_max - b.y_min), 1.0)
        return intersection / (area_a + area_b - intersection)

    @staticmethod
    def _preprocess_variants(image: np.ndarray) -> List[np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
        denoised = cv2.fastNlMeansDenoising(clahe, None, 8, 7, 21)

        adaptive = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            7,
        )

        sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(clahe, -1, sharpen_kernel)

        return [image, clahe, sharpened, adaptive]

    def extract_lines(self, image_path: str, conf_threshold: float = 0.25) -> List[OCRLine]:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image from {image_path}")

        lines: List[OCRLine] = []

        for variant in self._preprocess_variants(image):
            detections = self.reader.readtext(
                variant,
                detail=1,
                paragraph=False,
                rotation_info=[90, 180, 270],
                text_threshold=0.55,
                low_text=0.25,
                link_threshold=0.3,
                decoder="beamsearch",
            )

            for box, raw_text, conf in detections:
                text = self._normalize_text(raw_text)
                if not text or conf < conf_threshold:
                    continue
                lines.append(OCRLine(text=text, conf=float(conf), box=box))

        deduped: List[OCRLine] = []
        for candidate in sorted(lines, key=lambda item: item.conf, reverse=True):
            is_duplicate = False
            for existing in deduped:
                if self._iou(candidate, existing) >= 0.65 and (
                    candidate.text == existing.text
                    or Levenshtein.ratio(candidate.text.lower(), existing.text.lower()) > 0.85
                ):
                    is_duplicate = True
                    break
            if not is_duplicate:
                deduped.append(candidate)

        deduped.sort(key=lambda item: (round(item.y_center / 8.0), item.x_min))
        return deduped

    def _build_text_windows(self, sorted_lines: List[OCRLine]) -> List[str]:
        if not sorted_lines:
            return []

        windows: List[str] = []

        for idx, line in enumerate(sorted_lines):
            if not self._is_ingredient_header(line.text):
                continue

            chunk = [line.text]
            for follower in sorted_lines[idx + 1 : idx + 45]:
                if self._is_section_stop(follower.text) and len(chunk) > 2:
                    break
                chunk.append(follower.text)

            windows.append(" ".join(chunk))

        windows.append(" ".join(item.text for item in sorted_lines))
        return windows

    def extract_ingredient_candidates(self, image_path: str) -> List[str]:
        lines = self.extract_lines(image_path)
        windows = self._build_text_windows(lines)

        candidate_lists: List[List[str]] = []
        for window in windows:
            parsed = parse_ingredients_from_ocr(window)
            if parsed:
                candidate_lists.append(parsed)

        if not candidate_lists:
            return []

        candidate_lists.sort(key=lambda items: (len(items), sum(len(i) for i in items)), reverse=True)
        return candidate_lists[0]


def parse_ingredients_from_ocr(ocr_text: str) -> List[str]:
    if not ocr_text:
        return []

    ingredient_patterns = [
        r"ingredients\s*[:\-;]?\s*(.*?)(?=\b(?:directions|use|warning|caution|disclaimer|made in|for external use|how to use)\b|\Z)",
        r"ingredient[s]?[:\-;]?\s*(.*?)(?=\b(?:directions|use|warning|caution|disclaimer|made in|for external use|how to use)\b|\Z)",
        r"contains[:\-;]?\s*(.*?)(?=\b(?:directions|use|warning|caution|disclaimer|made in|for external use|how to use)\b|\Z)",
    ]

    ingredients_text = None
    for pattern in ingredient_patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE | re.DOTALL)
        if match:
            ingredients_text = match.group(1).strip()
            break

    if not ingredients_text:
        ingredients_text = ocr_text

    ingredients_text = re.sub(r"(\w+)\-\s*[\n\r]+\s*(\w+)", r"\1\2", ingredients_text)
    ingredients_text = re.sub(r"(\w+)\s+\-\s+(\w+)", r"\1-\2", ingredients_text)
    ingredients_text = re.sub(r"[\n\r]+", " ", ingredients_text)
    ingredients_text = re.sub(r"\s+", " ", ingredients_text)
    ingredients_text = re.sub(r"[;:]", ",", ingredients_text)
    ingredients_text = re.sub(r"\(\s+", "(", ingredients_text)
    ingredients_text = re.sub(r"\s+\)", ")", ingredients_text)

    comma_split = [item.strip() for item in ingredients_text.split(",")]
    processed_items = []

    for item in comma_split:
        if not item or len(item) <= 2:
            continue

        protected_item = item
        common_abbrev = ["vit.", "var.", "spp.", "sp.", "subsp.", "vol.", "no.", "dr.", "st."]

        for abbrev in common_abbrev:
            pattern = re.compile(re.escape(abbrev), re.IGNORECASE)
            protected_item = pattern.sub(lambda m: m.group().replace(".", "@"), protected_item)

        split_by_period = re.split(r"(\.\s+)(?=[A-Z])", protected_item)

        parts = []
        for i in range(0, len(split_by_period), 2):
            part = split_by_period[i]
            if i + 1 < len(split_by_period):
                part += "."
            parts.append(part)

        if not parts:
            parts = [protected_item]

        for part in parts:
            part = part.replace("@", ".")
            subparts = []
            matches = list(re.finditer(r"([a-z])([A-Z][a-z])", part))

            if matches:
                valid_splits = []

                for match in matches:
                    idx = match.start() + 1

                    open_parens = part[:idx].count("(")
                    close_parens = part[:idx].count(")")
                    if open_parens > close_parens:
                        continue

                    prefix_context = part[max(0, idx - 6) : idx].lower()
                    if any(prefix in prefix_context for prefix in ["di", "tri", "tetra", "poly", "mono", "iso"]):
                        continue

                    context = part[max(0, idx - 10) : min(len(part), idx + 10)]
                    if any(pattern in context.lower() for pattern in ["vitamin", "extract", "oil"]):
                        continue

                    valid_splits.append(idx)

                if valid_splits:
                    start_idx = 0
                    for idx in valid_splits:
                        subpart = part[start_idx:idx].strip()
                        if subpart:
                            subparts.append(subpart)
                        start_idx = idx

                    if start_idx < len(part):
                        subparts.append(part[start_idx:].strip())
                else:
                    subparts.append(part)
            else:
                subparts.append(part)

            processed_items.extend(subparts)

    final_ingredients = []

    for ing in processed_items:
        ing = ing.strip()
        ing = re.sub(r"^[^a-zA-Z0-9(]+|[^a-zA-Z0-9)]+$", "", ing)
        ing = re.sub(r"\s+", " ", ing)
        ing = re.sub(r"([A-Za-z])l([0-9])", r"\1-\2", ing)
        ing = re.sub(r"([A-Za-z])O([0-9])", r"\1-\2", ing)

        if ing and len(ing) > 1:
            final_ingredients.append(ing)

    return final_ingredients


def smart_analyze(ingredient, ewg):
    result = ewg.analyze_ingredient(ingredient)

    if result["ingredient_found"] and result.get("exact_match", False):
        return {
            "original": ingredient,
            "corrected": ingredient,
            "match_type": "exact",
            "data": result,
        }

    words = re.split(r"[\s,/\-]+", ingredient)
    words = [w for w in words if len(w) > 2 and w.lower() not in ["and", "with", "plus", "the"]]

    if len(words) > 1:
        found_matches = []

        for word in words:
            result = ewg.analyze_ingredient(word)

            if result["ingredient_found"] and result.get("exact_match", False):
                found_matches.append(
                    {
                        "original": word,
                        "corrected": word,
                        "match_type": "split_exact",
                        "data": result,
                    }
                )

        if found_matches:
            return found_matches[0]

    result = EWGSkindeepAPI().get_ingredient_data(ingredient, exact_match_only=False)

    if result["ingredient_found"]:
        return {
            "original": ingredient,
            "corrected": result["ingredient_info"]["name"],
            "match_type": "fuzzy",
            "data": result,
        }

    return {
        "original": ingredient,
        "corrected": None,
        "match_type": "no_match",
        "data": None,
    }


def smart_analyze_list(ingredient_list, ewg):
    results = []
    unmatched = []

    print("PHASE 1: Testing direct matches...")
    for ingredient in ingredient_list:
        result = smart_analyze(ingredient, ewg)

        if result["match_type"] in ["exact", "fuzzy"]:
            print(f"✓ Found match for: {ingredient}")
            results.append(result)
        else:
            print(f"✗ No match for: {ingredient}")
            unmatched.append(ingredient)

    print("\nPHASE 2: Testing combinations of adjacent unmatched ingredients...")
    if len(unmatched) >= 2:
        i = 0
        while i < len(unmatched) - 1:
            combined = unmatched[i] + " " + unmatched[i + 1]
            combined_result = ewg.analyze_ingredient(combined)

            if combined_result["ingredient_found"] and combined_result.get("exact_match", False):
                print(f"✓ Found exact match for combined: {combined}")
                results.append(
                    {
                        "original": f"{unmatched[i]} + {unmatched[i+1]}",
                        "corrected": combined,
                        "match_type": "combined_exact",
                        "data": combined_result,
                    }
                )
                i += 2
            else:
                combined_comma = unmatched[i] + ", " + unmatched[i + 1]
                comma_result = ewg.analyze_ingredient(combined_comma)

                if comma_result["ingredient_found"] and comma_result.get("exact_match", False):
                    print(f"✓ Found exact match for combined with comma: {combined_comma}")
                    results.append(
                        {
                            "original": f"{unmatched[i]} + {unmatched[i+1]}",
                            "corrected": combined_comma,
                            "match_type": "combined_comma_exact",
                            "data": comma_result,
                        }
                    )
                    i += 2
                else:
                    i += 1

        while i < len(unmatched):
            fuzzy_result = ewg.get_ingredient_data(unmatched[i], exact_match_only=False)

            if fuzzy_result["ingredient_found"]:
                print(f"~ Found closest match for: {unmatched[i]} -> {fuzzy_result['ingredient_info']['name']}")
                results.append(
                    {
                        "original": unmatched[i],
                        "corrected": fuzzy_result["ingredient_info"]["name"],
                        "match_type": "final_fuzzy",
                        "data": fuzzy_result,
                    }
                )
            else:
                print(f"✗ Could not find any match for: {unmatched[i]}")
                results.append(
                    {
                        "original": unmatched[i],
                        "corrected": None,
                        "match_type": "no_match",
                        "data": None,
                    }
                )
            i += 1

    return results


def pretty_print_ingredient(result):
    if not result or result.get("match_type") == "no_match":
        print("✗ No match found")
        return

    data = result.get("data", {})

    if isinstance(result, list):
        print("Multiple matches found from splitting:")
        for split_result in result:
            print(f"- {split_result['corrected']} (split from original)")
        return

    original = result.get("original", "Unknown")
    corrected = result.get("corrected", "Unknown")
    match_type = result.get("match_type", "Unknown")

    print(f"Original: {original}")

    if original != corrected and corrected:
        print(f"Corrected: {corrected}")

    print(f"Match type: {match_type}")

    if data and "ingredient_info" in data:
        info = data["ingredient_info"]

        if "score_range" in info:
            print(f"Score Range: {info['score_range']}")

        if "data_level" in info:
            print(f"Data Level: {info['data_level']}")

        if "concerns" in info and info["concerns"]:
            print("\nConcerns:")
            for concern in info["concerns"]:
                print(f"- {concern['concern']} [{concern['reference']}]")


def run_pipeline(image_path: str) -> List[str]:
    use_gpu = False
    try:
        import torch

        use_gpu = torch.cuda.is_available()
    except Exception:
        use_gpu = False

    extractor = RobustIngredientOCR(use_gpu=use_gpu)
    return extractor.extract_ingredient_candidates(image_path)


if __name__ == "__main__":
    ingredients = run_pipeline("product_images/image2.jpeg")
    print(f"Extracted ingredients ({len(ingredients)}):")
    print(ingredients)

    ewg = EWGSkindeepAPI()
    analysis_results = smart_analyze_list(ingredients, ewg)
    for ingredient_result in analysis_results:
        pretty_print_ingredient(ingredient_result)

    print("###")
