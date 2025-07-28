#!/usr/bin/env python3
"""
S3 Browser - A simple S3-compatible browser with CLI and web interfaces.
"""

import sys
import argparse
from s3_browser.cli import CLIInterface
from s3_browser.web import WebInterface


def main():
    """Main entry point for the S3 Browser application."""
    parser = argparse.ArgumentParser(
        description="S3 Browser - Browse S3-compatible storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  s3_browser.py cli                    # Start CLI mode
  s3_browser.py web                    # Start web mode
  s3_browser.py cli --bucket my-bucket # Start CLI with specific bucket
  s3_browser.py web --port 8080        # Start web mode on port 8080
        """
    )

    parser.add_argument('mode', choices=['cli', 'web'], help='Interface mode to use')

    # Common arguments
    parser.add_argument('--access-key', help='S3 access key (or set AWS_ACCESS_KEY_ID env var)')
    parser.add_argument('--secret-key', help='S3 secret key (or set AWS_SECRET_ACCESS_KEY env var)')
    parser.add_argument('--region', default='us-east-1', help='S3 region (default: us-east-1)')
    parser.add_argument('--endpoint-url', help='Custom S3 endpoint URL')

    # CLI-specific arguments
    parser.add_argument('--bucket', help='Default bucket to browse (CLI mode only)')

    # Web-specific arguments
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (web mode only, default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (web mode only, default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (web mode only)')

    args = parser.parse_args()
    
    # Create S3 client configuration
    s3_config = {
        'access_key': args.access_key,
        'secret_key': args.secret_key,
        'region': args.region,
        'endpoint_url': args.endpoint_url
    }

    try:
        if args.mode == 'cli':
            cli = CLIInterface(s3_config)
            cli.run(default_bucket=args.bucket)
        elif args.mode == 'web':
            web = WebInterface(s3_config)
            web.run(host=args.host, port=args.port, debug=args.debug)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
