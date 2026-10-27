"""Image handling: local folder by default, S3 when S3_BUCKET_NAME is set."""
import uuid
from pathlib import Path
from app.config import settings

IMAGES_DIR = Path(__file__).resolve().parent.parent / "static" / "images"
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BYTES = 2 * 1024 * 1024


def image_url(filename):
    """Build the public URL of a product image (local / S3 / CloudFront)."""
    if not filename:
        return "/static/images/placeholder.svg"
    if filename.startswith("http"):
        return filename
    if settings.IMAGE_BASE_URL:
        return f"{settings.IMAGE_BASE_URL}/{filename}"
    if settings.S3_BUCKET_NAME and settings.AWS_REGION:
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
    return f"/static/images/{filename}"


def save_image(upload) -> str:
    """Validate and store an uploaded image. Returns the stored filename."""
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT or not (upload.content_type or "").startswith("image/"):
        raise ValueError("Only JPG, PNG, WEBP or GIF images are allowed.")
    data = upload.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Image must be smaller than 2 MB.")
    name = uuid.uuid4().hex + ext
    if settings.S3_BUCKET_NAME:
        import boto3  # credentials come from the EC2 IAM Role, never from code
        boto3.client("s3", region_name=settings.AWS_REGION or None).put_object(
            Bucket=settings.S3_BUCKET_NAME, Key=name, Body=data, ContentType=upload.content_type
        )
    else:
        (IMAGES_DIR / name).write_bytes(data)
    return name
