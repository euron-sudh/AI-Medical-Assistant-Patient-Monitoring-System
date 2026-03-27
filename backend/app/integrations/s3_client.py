"""S3/MinIO file storage integration for medical report uploads.

Supports AWS S3, MinIO, and Google Cloud Storage (via S3 interop).
Reads configuration from environment variables via app.config.

Task #28 — Vikash Kumar
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import BaseConfig

logger = logging.getLogger(__name__)

__all__ = ["S3Client", "s3_client"]


class S3Client:
    """Client for S3-compatible object storage (AWS S3, MinIO, GCS interop).

    Methods:
        upload_file   — store bytes and return the object URL
        download_file — retrieve bytes from a stored object
        generate_presigned_url — create a temporary download link
        delete_file   — remove an object from the bucket
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket_name: str | None = None,
        region: str | None = None,
    ) -> None:
        self._endpoint_url = endpoint_url or BaseConfig.S3_ENDPOINT_URL or None
        self._access_key = access_key or BaseConfig.AWS_ACCESS_KEY_ID
        self._secret_key = secret_key or BaseConfig.AWS_SECRET_ACCESS_KEY
        self._bucket_name = bucket_name or BaseConfig.S3_BUCKET_NAME
        self._region = region or BaseConfig.AWS_REGION

        # Detect GCS interop mode
        self._is_gcs = (
            self._endpoint_url is not None
            and "storage.googleapis.com" in self._endpoint_url
        )

        client_kwargs: dict = {
            "service_name": "s3",
            "region_name": self._region,
            "aws_access_key_id": self._access_key,
            "aws_secret_access_key": self._secret_key,
            "config": BotoConfig(signature_version="s3v4"),
        }

        if self._endpoint_url:
            client_kwargs["endpoint_url"] = self._endpoint_url

        self._client = boto3.client(**client_kwargs)
        logger.info(
            "S3Client initialized bucket=%s endpoint=%s gcs=%s",
            self._bucket_name,
            self._endpoint_url or "AWS default",
            self._is_gcs,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload_file(
        self,
        file_bytes: bytes,
        patient_id: str,
        file_type: str = "pdf",
    ) -> str:
        """Upload a file to S3 and return the stored object URL.

        Args:
            file_bytes: Raw bytes of the file to upload.
            patient_id: Patient UUID — used as a prefix in the object key.
            file_type: File extension / MIME hint (e.g. 'pdf', 'png').

        Returns:
            The S3 object URL (s3://<bucket>/<key>).
        """
        key = self._build_key(patient_id, file_type)
        content_type = self._mime_type(file_type)

        try:
            self._client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            file_url = f"s3://{self._bucket_name}/{key}"
            logger.info("Uploaded %s (%d bytes)", file_url, len(file_bytes))
            return file_url
        except ClientError:
            logger.exception("Failed to upload file for patient %s", patient_id)
            raise

    def download_file(self, file_url: str) -> bytes:
        """Download a file from S3 given its object URL.

        Args:
            file_url: S3 URL in the form ``s3://<bucket>/<key>``.

        Returns:
            Raw bytes of the object.
        """
        bucket, key = self._parse_url(file_url)
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            data: bytes = response["Body"].read()
            logger.info("Downloaded %s (%d bytes)", file_url, len(data))
            return data
        except ClientError:
            logger.exception("Failed to download %s", file_url)
            raise

    def generate_presigned_url(self, file_url: str, expiry: int = 900) -> str:
        """Generate a temporary pre-signed URL for downloading a file.

        Args:
            file_url: S3 URL in the form ``s3://<bucket>/<key>``.
            expiry: URL lifetime in seconds (default 15 minutes).

        Returns:
            HTTPS pre-signed URL.
        """
        bucket, key = self._parse_url(file_url)
        try:
            url: str = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expiry,
            )
            logger.info("Generated presigned URL for %s (expiry=%ds)", file_url, expiry)
            return url
        except ClientError:
            logger.exception("Failed to generate presigned URL for %s", file_url)
            raise

    def delete_file(self, file_url: str) -> None:
        """Delete a file from S3.

        Args:
            file_url: S3 URL in the form ``s3://<bucket>/<key>``.
        """
        bucket, key = self._parse_url(file_url)
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            logger.info("Deleted %s", file_url)
        except ClientError:
            logger.exception("Failed to delete %s", file_url)
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_key(patient_id: str, file_type: str) -> str:
        """Build a unique object key: ``reports/<patient_id>/<uuid>.<ext>``."""
        unique = uuid.uuid4().hex
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        ext = file_type.lower().lstrip(".")
        return f"reports/{patient_id}/{ts}_{unique}.{ext}"

    @staticmethod
    def _parse_url(file_url: str) -> tuple[str, str]:
        """Parse ``s3://<bucket>/<key>`` into (bucket, key).

        Also handles plain ``<bucket>/<key>`` for convenience.
        """
        url = file_url
        if url.startswith("s3://"):
            url = url[5:]
        parts = url.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URL: {file_url}")
        return parts[0], parts[1]

    @staticmethod
    def _mime_type(file_type: str) -> str:
        """Map common file types to MIME types."""
        mapping = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "tiff": "image/tiff",
            "tif": "image/tiff",
            "dicom": "application/dicom",
            "dcm": "application/dicom",
            "txt": "text/plain",
            "csv": "text/csv",
            "json": "application/json",
        }
        return mapping.get(file_type.lower().lstrip("."), "application/octet-stream")


# Module-level singleton — import and use across the application
s3_client = S3Client()
