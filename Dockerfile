# ============================================================================
# Dockerfile for PCI Evidence Collector
# TWN-Style: Containerized Python collector
# ============================================================================

FROM python:3.11-slim

LABEL maintainer="GRC Engineering Team"
LABEL description="PCI DSS Evidence Collector Container"

# Set working directory
WORKDIR /app

# Install dependencies
COPY evidence/collectors/python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy collector script
COPY evidence/collectors/python/evidence_collect_basic.py .

# Create output directory
RUN mkdir -p /output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
ENTRYPOINT ["python3", "evidence_collect_basic.py"]
CMD ["--help"]

# Usage:
# docker build -t pci-evidence-collector .
# docker run --rm \
#   -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
#   -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
#   -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
#   -v $(pwd)/output:/output \
#   pci-evidence-collector \
#   --region us-west-2 \
#   --evidence-bucket <BUCKET> \
#   --prefix baseline/$(date +%F)
