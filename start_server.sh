#!/bin/bash
# Start Live VLM WebUI Server with HTTPS

cd "$(dirname "$0")"

# Detect and activate virtual environment if needed
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    # Check for .venv (preferred)
    if [ -d ".venv" ]; then
        echo "Activating .venv virtual environment..."
        source .venv/bin/activate
        echo ""
    # Check for venv (alternative)
    elif [ -d "venv" ]; then
        echo "Activating venv virtual environment..."
        source venv/bin/activate
        echo ""
    else
        echo "⚠️  No virtual environment detected!"
        echo "Please create one first:"
        echo "  python3 -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -r requirements.txt"
        echo ""
        echo "Or activate your conda environment:"
        echo "  conda activate live-vlm-webui"
        exit 1
    fi
fi

# Check if certificates exist
if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
    echo "Certificates not found. Generating..."
    ./generate_cert.sh
    echo ""
fi

# Start server with HTTPS
echo "Starting Live VLM WebUI server..."
echo "Auto-detecting local VLM services (Ollama, vLLM, SGLang)..."
echo "Will fall back to NVIDIA API Catalog if none found"
echo ""
echo "⚠️  Your browser will show a security warning (self-signed certificate)"
echo "    Click 'Advanced' → 'Proceed to localhost' (or 'Accept Risk')"
echo ""

# Run server with auto-detection (no --model or --api-base specified)
# To override, use: ./start_server.sh --model YOUR_MODEL --api-base YOUR_API
python server.py \
  --ssl-cert cert.pem \
  --ssl-key key.pem \
  --host 0.0.0.0 \
  --port 8080 \
  "$@"

