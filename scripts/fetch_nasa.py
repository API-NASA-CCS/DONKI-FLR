"""Fetch solar-flare events from NASA DONKI and upsert them into Supabase."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NASA_ENDPOINT = "https://api.nasa.gov/DONKI/FLR"
TABLE_EVENTS = "flares"
TABLE_RUNS = "execucoes"
BATCH_SIZE = 100
HTTP_TIMEOUT = 30


def request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
                 body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=data, headers=headers or {}, method=method)
    with urlopen(request, timeout=HTTP_TIMEOUT) as response:
        payload = response.read()
    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def iso_or_none(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return None


def normalize_event(event: dict[str, Any], collected_at: str) -> dict[str, Any] | None:
    flr_id = event.get("flrID") or event.get("activityID")
    if not flr_id:
        return None
    return {
        "flr_id": str(flr_id),
        "catalog": event.get("catalog"),
        "begin_time": iso_or_none(event.get("beginTime") or event.get("begineTime")),
        "peak_time": iso_or_none(event.get("peakTime")),
        "end_time": iso_or_none(event.get("endTime")),
        "class_type": event.get("classType"),
        "source_location": event.get("sourceLocation"),
        "active_region_num": event.get("activeRegionNum"),
        "submission_time": iso_or_none(event.get("submissionTime")),
        "note": event.get("note"),
        "link": event.get("link"),
        "instruments": event.get("instruments") or [],
        "linked_events": event.get("linkedEvents") or [],
        "raw_payload": event,
        "collected_at": collected_at,
    }


def unique_events(events: list[dict[str, Any]], collected_at: str) -> list[dict[str, Any]]:
    """Deduplicate by natural key before PostgREST upsert (avoids PG 21000)."""
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        row = normalize_event(event, collected_at)
        if row:
            by_id[row["flr_id"]] = row
    return list(by_id.values())


def supabase_headers(service_key: str, *, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def supabase_rest(base_url: str, table: str) -> str:
    return f"{base_url.rstrip('/')}/rest/v1/{table}"


def upsert_batch(base_url: str, service_key: str, rows: list[dict[str, Any]]) -> None:
    query = urlencode({"on_conflict": "flr_id"})
    request_json(
        f"{supabase_rest(base_url, TABLE_EVENTS)}?{query}",
        method="POST",
        headers=supabase_headers(service_key, prefer="resolution=merge-duplicates,return=minimal"),
        body=rows,
    )


def write_run(base_url: str, service_key: str, started_at: str, *, status: str,
              processed: int, batches: int, errors: list[str], finished_at: str) -> None:
    row = {
        "iniciado_em": started_at,
        "finalizado_em": finished_at,
        "registros_processados": processed,
        "lotes": batches,
        "erros": errors,
        "status": status,
    }
    request_json(
        supabase_rest(base_url, TABLE_RUNS),
        method="POST",
        headers=supabase_headers(service_key, prefer="return=minimal"),
        body=[row],
    )


def main() -> int:
    started = datetime.now(timezone.utc)
    started_iso = started.isoformat().replace("+00:00", "Z")
    api_key = os.getenv("NASA_API_KEY", "").strip()
    base_url = os.getenv("SUPABASE_URL", "").strip()
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    errors: list[str] = []
    processed = batches = 0
    status = "concluido"

    if not api_key or not base_url or not service_key:
        missing = [name for name, value in (("NASA_API_KEY", api_key),
                   ("SUPABASE_URL", base_url), ("SUPABASE_SERVICE_KEY", service_key)) if not value]
        print(f"Configuração ausente: {', '.join(missing)}", file=sys.stderr)
        return 2

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=30)
    params = urlencode({
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "api_key": api_key,
    })
    collected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        events = request_json(f"{NASA_ENDPOINT}?{params}")
        if not isinstance(events, list):
            raise ValueError("A resposta da NASA não foi uma lista de eventos.")
        rows = unique_events(events, collected_at)
        processed = len(rows)
        for offset in range(0, len(rows), BATCH_SIZE):
            batch = rows[offset:offset + BATCH_SIZE]
            try:
                upsert_batch(base_url, service_key, batch)
                batches += 1
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                errors.append(f"Lote {offset // BATCH_SIZE + 1}: {exc}")
                print(errors[-1], file=sys.stderr)
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"Coleta: {exc}")
        print(errors[-1], file=sys.stderr)

    if errors:
        status = "erro_parcial" if batches else "erro_critico"
    finished_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        write_run(base_url, service_key, started_iso, status=status,
                  processed=processed, batches=batches, errors=errors, finished_at=finished_iso)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"Não foi possível registrar a execução no Supabase: {exc}", file=sys.stderr)
        return 1

    print(f"Status: {status}; registros: {processed}; lotes: {batches}; erros: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
