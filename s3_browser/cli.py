"""
CLI interface for S3 Browser.
"""

import os
import cmd
import shlex
from typing import Dict, Optional
from .classes.s3_client import S3Client


class CLIInterface(cmd.Cmd):
    """Interactive CLI interface for browsing S3 buckets and objects."""

    intro = """
S3 Browser CLI - Interactive S3-compatible storage browser
Type 'help' for available commands, 'quit' to exit.
"""
    prompt = 's3browser> '

    def __init__(self, s3_config: Dict):
        """Initialize CLI interface with S3 configuration."""
        super().__init__()
        self.s3_client = S3Client(**s3_config)
        self.current_bucket = None
        self.current_prefix = ''
        self._pagination = {}  # {(bucket, prefix): {'token': None, 'prev': []}}
        
        # Test connection
        if not self.s3_client.test_connection():
            print("Warning: Could not connect to S3. Check your credentials.")

    def run(self, default_bucket: Optional[str] = None):
        """Run the CLI interface."""
        if default_bucket:
            self.current_bucket = default_bucket
            self.current_prefix = ''
            print(f"Default bucket set to: {default_bucket}")
        
        self.cmdloop()

    def do_buckets(self, arg):
        """List all available buckets."""
        try:
            buckets = self.s3_client.list_buckets()
            if not buckets:
                print("No buckets found.")
                return
            
            print("\nAvailable buckets:")
            print("-" * 50)
            for bucket in buckets:
                print(f"  {bucket['name']} (created: {bucket['creation_date']})")
            print()

        except Exception as e:
            print(f"Error listing buckets: {e}")

    def do_use(self, bucket_name):
        """Switch to a specific bucket: use <bucket_name>"""
        if not bucket_name:
            print("Usage: use <bucket_name>")
            return

        try:
            # Test if bucket exists by trying to list objects
            self.s3_client.list_objects(bucket_name, '', '')
            self.current_bucket = bucket_name
            self.current_prefix = ''
            print(f"Switched to bucket: {bucket_name}")
            self.prompt = f's3browser:{bucket_name}> '
            
        except Exception as e:
            print(f"Error switching to bucket '{bucket_name}': {e}")

    def do_ls(self, arg):
        """List objects and prefixes in current bucket: ls [prefix] [--next|--prev] [--contains STR] [--min-size N] [--max-size N] [--after DATE] [--before DATE] [--sort FIELD] [--desc]"""
        if not self.current_bucket:
            print("No bucket selected. Use 'use <bucket_name>' first.")
            return

        args = shlex.split(arg)
        prefix = self.current_prefix
        nav = None
        filters = {
            'key_substring': None,
            'min_size': None,
            'max_size': None,
            'modified_after': None,
            'modified_before': None,
            'sort_by': None,
            'sort_order': 'asc',
        }
        i = 0
        while i < len(args):
            a = args[i]
            if a == '--next':
                nav = 'next'
            elif a == '--prev':
                nav = 'prev'
            elif a == '--contains' and i+1 < len(args):
                filters['key_substring'] = args[i+1]
                i += 1
            elif a == '--min-size' and i+1 < len(args):
                filters['min_size'] = int(args[i+1])
                i += 1
            elif a == '--max-size' and i+1 < len(args):
                filters['max_size'] = int(args[i+1])
                i += 1
            elif a == '--after' and i+1 < len(args):
                filters['modified_after'] = args[i+1]
                i += 1
            elif a == '--before' and i+1 < len(args):
                filters['modified_before'] = args[i+1]
                i += 1
            elif a == '--sort' and i+1 < len(args):
                filters['sort_by'] = args[i+1]
                i += 1
            elif a == '--desc':
                filters['sort_order'] = 'desc'
            elif not a.startswith('--'):
                prefix = a
            i += 1

        key = (self.current_bucket, prefix)
        pagestate = self._pagination.setdefault(key, {'token': None, 'prev': []})
        
        if nav == 'next' and pagestate['token']:
            pagestate['prev'].append(pagestate['token'])
        elif nav == 'prev' and pagestate['prev']:
            pagestate['token'] = pagestate['prev'].pop()
        elif nav:
            print("No more pages in that direction.")
            return
        else:
            pagestate['token'] = None
            pagestate['prev'] = []

        try:
            objects, prefixes, next_token = self.s3_client.list_objects(
                self.current_bucket, prefix, max_keys=20, continuation_token=pagestate['token'],
                key_substring=filters['key_substring'],
                min_size=filters['min_size'],
                max_size=filters['max_size'],
                modified_after=filters['modified_after'],
                modified_before=filters['modified_before'],
                sort_by=filters['sort_by'],
                sort_order=filters['sort_order'],
            )
            pagestate['token'] = next_token

            print(f"\nContents of s3://{self.current_bucket}/{prefix}")
            print("-" * 60)

            # Show prefixes (folders)
            for prefix_name in prefixes:
                print(f"  📁 {prefix_name}")

            # Show objects (files)
            for obj in objects:
                size_str = self._format_size(obj['size'])
                print(f"  📄 {obj['key']} ({size_str})")

            if not objects and not prefixes:
                print("  (empty)")
            print()

            if pagestate['token']:
                print("Type 'ls --next' for next page.")
            if pagestate['prev']:
                print("Type 'ls --prev' for previous page.")

        except Exception as e:
            print(f"Error listing objects: {e}")

    def do_cd(self, prefix):
        """Change directory (prefix): cd <prefix> or cd .."""
        if not self.current_bucket:
            print("No bucket selected. Use 'use <bucket_name>' first.")
            return

        if prefix == '..':
            # Go up one level
            if self.current_prefix:
                parts = self.current_prefix.rstrip('/').split('/')
                if len(parts) > 1:
                    self.current_prefix = '/'.join(parts[:-1]) + '/'
                else:
                    self.current_prefix = ''
                print(f"Current prefix: {self.current_prefix or '/'}")
            return

        if not prefix:
            print("Usage: cd <prefix> or cd ..")
            return

        # Ensure prefix ends with /
        if not prefix.endswith('/'):
            prefix += '/'

        self.current_prefix = prefix
        print(f"Current prefix: {prefix}")

    def do_info(self, key):
        """Get detailed information about an object: info <key>"""
        if not self.current_bucket:
            print("No bucket selected. Use 'use <bucket_name>' first.")
            return

        if not key:
            print("Usage: info <key>")
            return

        try:
            info = self.s3_client.get_object_info(self.current_bucket, key)
            print(f"\nObject: s3://{self.current_bucket}/{key}")
            print("-" * 50)
            print(f"Size: {self._format_size(info['size'])}")
            print(f"Last Modified: {info['last_modified']}")
            print(f"ETag: {info['etag']}")
            print(f"Content Type: {info['content_type']}")
            
            if info['metadata']:
                print("Metadata:")
                for k, v in info['metadata'].items():
                    print(f"  {k}: {v}")
            print()
            
        except Exception as e:
            print(f"Error getting object info: {e}")

    def do_pwd(self, arg):
        """Show current bucket and prefix."""
        if self.current_bucket:
            prefix = self.current_prefix or '/'
            print(f"s3://{self.current_bucket}{prefix}")
        else:
            print("No bucket selected.")

    def do_clear(self, arg):
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_quit(self, arg):
        """Exit the application."""
        print("Goodbye!")
        return True

    def do_exit(self, arg):
        """Exit the application."""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """Exit on EOF (Ctrl+D)."""
        print()
        return self.do_quit(arg)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def default(self, line):
        """Handle unknown commands."""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands.")

    def emptyline(self):
        """Do nothing on empty line."""
        pass
