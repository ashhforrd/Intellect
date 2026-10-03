from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

import pytesseract
from PIL import Image
from pytesseract import Output, TesseractNotFoundError


class OcrError(Exception):
    """Raised when OCR processing fails."""


@dataclass(frozen=True, slots=True)
class OcrResult:
    text: str
    confidence: float | None


class OcrEngine(Protocol):
    def recognize(self, image_bytes: bytes) -> OcrResult:
        """Extract text from an image."""


class TesseractOcrEngine:
    def __init__(self, languages: str = "ind+eng") -> None:
        self._languages = languages

    def recognize(self, image_bytes: bytes) -> OcrResult:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                rgb_image = image.convert("RGB")

                data = pytesseract.image_to_data(
                    rgb_image,
                    lang=self._languages,
                    output_type=Output.DICT,
                )
        except TesseractNotFoundError as error:
            raise OcrError("Tesseract is not installed") from error
        except Exception as error:
            raise OcrError("OCR processing failed") from error

        lines: dict[tuple[int, int, int], list[str]] = defaultdict(list)
        confidence_values: list[float] = []

        for index, raw_text in enumerate(data["text"]):
            text = raw_text.strip()

            if not text:
                continue

            line_key = (
                data["block_num"][index],
                data["par_num"][index],
                data["line_num"][index],
            )
            lines[line_key].append(text)

            confidence = float(data["conf"][index])

            if confidence >= 0:
                confidence_values.append(confidence)

        extracted_text = "\n".join(" ".join(words) for words in lines.values()).strip()

        average_confidence = (
            sum(confidence_values) / len(confidence_values) / 100 if confidence_values else None
        )

        return OcrResult(
            text=extracted_text,
            confidence=average_confidence,
        )
