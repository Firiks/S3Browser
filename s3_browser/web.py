"""
Web interface for S3 Browser using FastAPI and Jinja2.
"""

import os
import uvicorn
from typing import Dict, Optional
from .classes.s3_client import S3Client
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse


class WebInterface:
    """Web interface for browsing S3 buckets and objects using FastAPI."""

    def __init__(self, s3_config: Dict):
        """Initialize web interface with S3 configuration."""
        self.app = FastAPI(title="S3 Browser")
        self.s3_client = S3Client(**s3_config)
        self._setup_routes()
        
        # Mount static files
        static_dir = os.path.join(os.path.dirname(__file__), 'assets', 'static')
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # Jinja2 templates
        templates_dir = os.path.join(os.path.dirname(__file__), 'assets', 'templates')
        self.templates = Jinja2Templates(directory=templates_dir)
    
    def _setup_routes(self):
        app = self.app
        templates = self.templates
        s3_client = self.s3_client

        @app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            try:
                buckets = s3_client.list_buckets()
                return templates.TemplateResponse('index.html', {"request": request, "buckets": buckets})
            except Exception as e:
                return templates.TemplateResponse('error.html', {"request": request, "error": str(e)})

        @app.get("/bucket/{bucket_name}", response_class=HTMLResponse)
        async def bucket_view(
            request: Request,
            bucket_name: str,
            prefix: str = Query('', alias='prefix'),
            max_keys: int = Query(20, alias='max_keys'),
            continuation_token: str = Query(None, alias='continuation_token'),
            key_substring: str = Query(None, alias='key_substring'),
            min_size: int = Query(None, alias='min_size'),
            max_size: int = Query(None, alias='max_size'),
            modified_after: str = Query(None, alias='modified_after'),
            modified_before: str = Query(None, alias='modified_before'),
            sort_by: str = Query(None, alias='sort_by'),
            sort_order: str = Query('asc', alias='sort_order'),
        ):
            try:
                objects, prefixes, next_token = s3_client.list_objects(
                    bucket_name, prefix, max_keys=max_keys, continuation_token=continuation_token,
                    key_substring=key_substring,
                    min_size=min_size,
                    max_size=max_size,
                    modified_after=modified_after,
                    modified_before=modified_before,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
                prev_token = request.query_params.get('prev_token')
                return templates.TemplateResponse('bucket.html', {
                    "request": request,
                    "bucket_name": bucket_name,
                    "objects": objects,
                    "prefixes": prefixes,
                    "current_prefix": prefix,
                    "next_token": next_token,
                    "prev_token": prev_token,
                    "max_keys": max_keys,
                    "continuation_token": continuation_token
                })
            except Exception as e:
                return templates.TemplateResponse('error.html', {"request": request, "error": str(e)})

        @app.get("/api/buckets", response_class=JSONResponse)
        async def api_buckets():
            try:
                buckets = s3_client.list_buckets()
                return {"buckets": buckets}
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/bucket/{bucket_name}", response_class=JSONResponse)
        async def api_bucket_contents(bucket_name: str, prefix: str = Query('', alias='prefix'), max_keys: int = Query(20, alias='max_keys'), continuation_token: str = Query(None, alias='continuation_token')):
            try:
                objects, prefixes, next_token = s3_client.list_objects(bucket_name, prefix, max_keys=max_keys, continuation_token=continuation_token)
                return {
                    "objects": objects,
                    "prefixes": prefixes,
                    "current_prefix": prefix,
                    "next_token": next_token
                }
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/object/{bucket_name}/{key:path}", response_class=JSONResponse)
        async def api_object_info(bucket_name: str, key: str):
            try:
                info = s3_client.get_object_info(bucket_name, key)
                return info
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the FastAPI application."""
        print(f"Starting S3 Browser web interface at http://{host}:{port}")
        print("Press Ctrl+C to stop")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=debug
        )
