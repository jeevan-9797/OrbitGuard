"""Smoke-test every operation exposed by a deployed OrbitGuard FastAPI app.

Usage:
    python test_live_api.py
    python test_live_api.py --base-url https://your-service.onrender.com

The script only needs httpx (already listed in requirements.txt).  Optional
authentication can be supplied with API_AUTH_TOKEN, API_AUTH_USERNAME, and
API_AUTH_PASSWORD environment variables if the deployed service protects the
documentation/API routes.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx


BASE_URL = "https://orbitguard-backend.onrender.com"  # Replace with your actual Render URL
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass
class CheckResult:
    method: str
    endpoint: str
    status_code: str
    elapsed_ms: float
    result: str
    detail: str = ""


def resolve_schema(schema: Any, document: dict[str, Any]) -> dict[str, Any]:
    """Resolve the small subset of JSON Schema commonly emitted by FastAPI."""
    if not isinstance(schema, dict):
        return {}
    if "$ref" in schema:
        value: Any = document
        for part in schema["$ref"].removeprefix("#/").split("/"):
            value = value.get(part, {}) if isinstance(value, dict) else {}
        return resolve_schema(value, document)
    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema and schema[key]:
            merged: dict[str, Any] = {}
            for item in schema[key]:
                merged.update(resolve_schema(item, document))
            merged.update({k: v for k, v in schema.items() if k not in {key}})
            return merged
    return schema


def example_for_schema(schema: Any, document: dict[str, Any]) -> Any:
    """Build a conservative mock value from an OpenAPI request schema."""
    schema = resolve_schema(schema, document)
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if schema.get("enum"):
        return schema["enum"][0]

    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            name: example_for_schema(child, document)
            for name, child in schema.get("properties", {}).items()
            if not (resolve_schema(child, document).get("readOnly"))
        }
    if schema_type == "array":
        return [example_for_schema(schema.get("items", {}), document)]
    if schema_type == "integer":
        return schema.get("minimum", 1)
    if schema_type == "number":
        return schema.get("minimum", 1.0)
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        fmt = schema.get("format")
        return {
            "uuid": "00000000-0000-0000-0000-000000000001",
            "date-time": "2026-01-01T00:00:00Z",
            "date": "2026-01-01",
            "email": "test@example.com",
        }.get(fmt, "test-value")
    return {}


def mock_path_value(name: str, schema: dict[str, Any], document: dict[str, Any]) -> str:
    value = example_for_schema(schema, document)
    if value not in ({}, None, ""):
        return str(value)
    lowered = name.lower()
    if "satellite" in lowered:
        return "SAT-01"
    if "incident" in lowered:
        return "ANO-MOCK"
    if "plan" in lowered:
        return "PLAN-MOCK"
    return "mock"


def format_endpoint(path: str, parameters: list[dict[str, Any]], document: dict[str, Any]) -> str:
    for parameter in parameters:
        if parameter.get("in") == "path":
            schema = resolve_schema(parameter.get("schema", {}), document)
            path = path.replace(
                "{" + parameter["name"] + "}",
                mock_path_value(parameter["name"], schema, document),
            )
    return path


def auth_options() -> tuple[dict[str, str], httpx.BasicAuth | None]:
    headers: dict[str, str] = {}
    token = os.getenv("API_AUTH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    username = os.getenv("API_AUTH_USERNAME")
    password = os.getenv("API_AUTH_PASSWORD")
    basic = httpx.BasicAuth(username, password) if username and password else None
    return headers, basic


def is_success(status_code: int) -> bool:
    return 200 <= status_code < 300


def request_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    json_body: Any = None,
    params: dict[str, Any] | None = None,
) -> tuple[int, float, httpx.Response | None, str]:
    started = time.perf_counter()
    try:
        response = client.request(method, url, json=json_body, params=params)
        elapsed = (time.perf_counter() - started) * 1000
        return response.status_code, elapsed, response, ""
    except httpx.HTTPError as exc:
        elapsed = (time.perf_counter() - started) * 1000
        return 0, elapsed, None, str(exc)


def request_stream_probe(
    client: httpx.Client, method: str, url: str
) -> tuple[int, float, str]:
    """Check a streaming endpoint by reading only its first event/chunk."""
    started = time.perf_counter()
    try:
        with client.stream(method, url) as response:
            next(response.iter_bytes())
            elapsed = (time.perf_counter() - started) * 1000
            return response.status_code, elapsed, ""
    except (httpx.HTTPError, StopIteration) as exc:
        elapsed = (time.perf_counter() - started) * 1000
        return 0, elapsed, str(exc) or "stream ended before sending an event"


def check_essential_routes(client: httpx.Client) -> list[CheckResult]:
    checks: list[CheckResult] = []

    status, elapsed, response, error = request_json(client, "GET", "/api/health")
    connected = False
    if response is not None:
        try:
            body = response.json()
            connected = body.get("services", {}).get("database") == "connected"
        except ValueError:
            pass
    checks.append(CheckResult("GET", "/api/health", str(status or "ERR"), elapsed,
                              "PASS" if status == 200 and connected else "FAIL",
                              error or ("database is not connected" if not connected else "")))

    for endpoint in ("/docs", "/openapi.json"):
        status, elapsed, _, error = request_json(client, "GET", endpoint)
        checks.append(CheckResult("GET", endpoint, str(status or "ERR"), elapsed,
                                  "PASS" if status == 200 else "FAIL", error))
    return checks


def discover_and_test(client: httpx.Client, schema: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for path, path_item in sorted(schema.get("paths", {}).items()):
        if not isinstance(path_item, dict):
            continue
        common_parameters = path_item.get("parameters", [])
        for method, operation in sorted(path_item.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            method = method.upper()
            parameters = common_parameters + operation.get("parameters", [])
            endpoint = format_endpoint(path, parameters, schema)
            query: dict[str, Any] = {}
            for parameter in parameters:
                if parameter.get("in") == "query":
                    parameter_schema = resolve_schema(parameter.get("schema", {}), schema)
                    if "default" in parameter_schema:
                        query[parameter["name"]] = parameter_schema["default"]
                    elif parameter.get("required"):
                        query[parameter["name"]] = example_for_schema(parameter_schema, schema)

            body = None
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {}) if isinstance(request_body, dict) else {}
            json_content = content.get("application/json") or content.get("application/*+json")
            if json_content:
                body = example_for_schema(json_content.get("schema", {}), schema)

            if method == "GET" and endpoint.startswith("/api/stream/"):
                status, elapsed, error = request_stream_probe(client, method, endpoint)
            else:
                status, elapsed, _, error = request_json(
                    client, method, endpoint, json_body=body, params=query
                )
            results.append(CheckResult(method, endpoint, str(status or "ERR"), elapsed,
                                       "PASS" if is_success(status) else "FAIL", error))
    return results


def print_table(results: list[CheckResult]) -> None:
    headers = ("Method", "Endpoint", "Status Code", "Response Time (ms)", "Result")
    rows = [headers] + [
        (r.method, r.endpoint, r.status_code, f"{r.elapsed_ms:.1f}", r.result) for r in results
    ]
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(headers))]
    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print("\n" + line)
    print("| " + " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(headers)) + " |")
    print(line)
    for row in rows[1:]:
        print("| " + " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)) + " |")
    print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", BASE_URL))
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    headers, basic_auth = auth_options()

    try:
        with httpx.Client(base_url=base_url, headers=headers, auth=basic_auth,
                          timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True) as client:
            status, elapsed, response, error = request_json(client, "GET", "/openapi.json")
            if status != 200 or response is None:
                print(f"Could not load {base_url}/openapi.json: {error or status}", file=sys.stderr)
                return 1
            try:
                schema = response.json()
            except ValueError as exc:
                print(f"OpenAPI response was not valid JSON: {exc}", file=sys.stderr)
                return 1

            essential_results = check_essential_routes(client)
            dynamic_results = discover_and_test(client, schema)
            essential_keys = {(result.method, result.endpoint) for result in essential_results}
            results = essential_results + [
                result for result in dynamic_results
                if (result.method, result.endpoint) not in essential_keys
            ]
    except httpx.HTTPError as exc:
        print(f"Could not connect to {base_url}: {exc}", file=sys.stderr)
        return 1

    print_table(results)
    passed = sum(result.result == "PASS" for result in results)
    failed = len(results) - passed
    print(f"Total Endpoints Tested: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
