# S3 Browser

A simple S3-compatible browser with both CLI and web interfaces for browsing buckets and objects.

## Features

- **CLI Mode**: Interactive command-line interface for browsing S3 buckets
- **Web Mode**: Modern web interface with Bootstrap styling
- **S3-Compatible**: Works with AWS S3 and other S3-compatible services (MinIO, Ceph, etc.)
- **Environment Support**: Supports dev, test, and prod environments
- **Clean Architecture**: Shared classes to avoid code duplication

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd S3Browser
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

You can set credentials using environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
export S3_ENDPOINT_URL=https://your-s3-endpoint.com  # Optional for custom endpoints
```

### Command Line Arguments

You can also pass credentials directly via command line arguments (see usage examples below).

## Usage

### CLI Mode

Start the interactive CLI interface:

```bash
# Basic usage
python s3_browser.py cli

# With specific credentials
python s3_browser.py cli --access-key YOUR_KEY --secret-key YOUR_SECRET

# With custom endpoint (for S3-compatible services)
python s3_browser.py cli --endpoint-url https://your-s3-endpoint.com

# Start with a specific bucket
python s3_browser.py cli --bucket my-bucket
```

#### CLI Commands

- `buckets` - List all available buckets
- `use <bucket_name>` - Switch to a specific bucket
- `ls [prefix]` - List objects and prefixes in current bucket
- `cd <prefix>` - Change directory (prefix)
- `cd ..` - Go up one level
- `info <key>` - Get detailed information about an object
- `pwd` - Show current bucket and prefix
- `clear` - Clear the screen
- `quit` or `exit` - Exit the application

### Web Mode

Start the web interface:

```bash
# Basic usage (defaults to http://127.0.0.1:5000)
python s3_browser.py web

# Custom host and port
python s3_browser.py web --host 0.0.0.0 --port 8080

# With debug mode
python s3_browser.py web --debug

# With custom credentials
python s3_browser.py web --access-key YOUR_KEY --secret-key YOUR_SECRET
```

The web interface provides:
- **Bucket List**: View all available buckets
- **Object Browser**: Navigate through folders and files
- **Object Details**: Click "Info" to view detailed object information
- **Responsive Design**: Works on desktop and mobile devices

## Examples

### AWS S3
```bash
python s3_browser.py cli --region us-west-2
```

### MinIO
```bash
python s3_browser.py web --endpoint-url http://localhost:9000
```

### Ceph
```bash
python s3_browser.py cli --endpoint-url https://ceph-cluster.com --region us-east-1
```

## Project Structure

```
S3Browser/
├── s3_browser.py              # Main entry point
├── requirements.txt            # Dependencies
├── README.md                  # This file
└── s3_browser/
    ├── __init__.py
    ├── cli.py                 # CLI interface
    ├── web.py                 # Web interface
    └── classes/
        ├── __init__.py
        └── s3_client.py       # Shared S3 client
```

## Development

The project follows clean architecture principles:

- **Shared Classes**: Common S3 operations in `s3_browser/classes/s3_client.py`
- **No Duplication**: Both CLI and web interfaces use the same S3 client
- **Environment Support**: Handles dev, test, and prod environments
- **Simple Solutions**: Avoids over-engineering

## Troubleshooting

### Connection Issues
- Verify your credentials are correct
- Check if the S3 endpoint is accessible
- Ensure proper network connectivity

### Permission Issues
- Verify your credentials have the necessary permissions
- Check bucket and object access policies

### Web Interface Issues
- Ensure port 5000 (or your chosen port) is available
- Check firewall settings if accessing remotely

## License

This project is open source and available under the MIT License. 