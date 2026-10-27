"""Prepare every PDF page or an oriented photo for model input."""
import base64
import io
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps, UnidentifiedImageError


def image_part(data: bytes, mime: str = 'image/png') -> dict:
    return {'inlineData': {'mimeType': mime, 'data': base64.b64encode(data).decode('ascii')}}


def load_pages(path: Path, dpi: int = 150) -> list[dict]:
    if not path.is_file():
        raise RuntimeError('Input file does not exist.')
    parts = []
    if path.suffix.lower() == '.pdf':
        try:
            with pdfium.PdfDocument(path) as document:
                if not len(document):
                    raise RuntimeError('PDF has no pages.')
                for index in range(len(document)):
                    page = document[index]
                    try:
                        bitmap = page.render(scale=dpi / 72)
                        try:
                            with bitmap.to_pil() as image, io.BytesIO() as buffer:
                                image.save(buffer, format='PNG')
                                parts.extend([{'text': f'Page {index + 1}'}, image_part(buffer.getvalue())])
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
        except pdfium.PdfiumError:
            raise RuntimeError('Cannot read PDF; check corruption or password protection.') from None
    elif path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
        try:
            with Image.open(path) as original:
                with ImageOps.exif_transpose(original) as oriented, io.BytesIO() as buffer:
                    oriented.convert('RGB').save(buffer, format='PNG')
                    parts.append(image_part(buffer.getvalue()))
        except (UnidentifiedImageError, OSError):
            raise RuntimeError('Cannot read image.') from None
    else:
        raise RuntimeError('Unsupported format; use PDF, JPG, JPEG, or PNG.')
    return parts
