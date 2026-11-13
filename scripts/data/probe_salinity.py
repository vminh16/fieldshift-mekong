#!/usr/bin/env python3
"""Probe public SIWRR bulletins + MRC endpoints. Never invent point salinity.

--download-bulletin saves a cited PDF for manual observation/date/unit review.
Outputs site JSON with salinity=null and the actual access evidence.
stdlib + httpx only; no credentials needed or sent.
"""

import argparse
import hashlib
import time
from pathlib import Path

import httpx
from common import DEFAULT_CACHE, SITES, envelope, write_json

URLS = {
    "siwrr_bulletin_page": "https://www.siwrr.org.vn/?gid=540&id=1536&lang=&page=1",
    "siwrr_pdf": "https://www.siwrr.org.vn/docs/2023/files/20251124-Ban-tin-mua-kho-2025-2026-DB-HTVH-CL-CB-24-11-2025.pdf",
    "siwrr_observations_pdf": "https://www.siwrr.org.vn/docs/2023/files/20260504-BC-danh-gia-va-du-bao-moi-truong-nuoc-Vam-Co-Ngay-lay-mau-18_04_2026--Du-bao-29_04_2026.pdf",
    "siwrp_dbscl": "https://siwrp.org.vn/news/khu-vuc-dbscl_435.html",
    "mrc_portal": "https://portal.mrcmekong.org/",
    "mrc_swagger": "https://data-services.mrcmekong.org/",
    "mrc_water_quality": "https://data-services.mrcmekong.org/api/v1/hfwqm",
    "mrc_water_quality_csv": "https://data-services.mrcmekong.org/api/v1/hfwqm/export",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--download-bulletin", action="store_true")
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()
    observations = []
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        for name, url in URLS.items():
            start = time.monotonic()
            result = {"name": name, "url": url}
            try:
                r = client.get(url)
                result.update(
                    status=r.status_code,
                    final_url=str(r.url),
                    size_bytes=len(r.content),
                    content_type=r.headers.get("content-type"),
                )
                if name in ("siwrr_pdf", "siwrr_observations_pdf"):
                    result["pdf_signature_valid"] = r.content.startswith(b"%PDF-")
                    result["sha256"] = hashlib.sha256(r.content).hexdigest()
                    if (
                        args.download_bulletin
                        and r.status_code == 200
                        and result["pdf_signature_valid"]
                    ):
                        filename = (
                            "siwrr-2025-11-24.pdf"
                            if name == "siwrr_pdf"
                            else "siwrr-vamco-2026-04.pdf"
                        )
                        out = args.cache_root / "salinity" / "bulletins" / filename
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(r.content)
                else:
                    result["body_preview"] = r.text[:400]
            except httpx.HTTPError as exc:
                result["error"] = str(exc)
            result["seconds"] = round(time.monotonic() - start, 3)
            observations.append(result)
            print(f"{name}: {result.get('status', result.get('error'))}", flush=True)
    for site in SITES:
        write_json(
            args.cache_root / "salinity" / f"{site}.json",
            envelope(
                "public_salinity_access_audit",
                site,
                status="UNAVAILABLE",
                evidence_kind=None,
                salinity=None,
                unit=None,
                reason="NO_VERIFIED_MACHINE_READABLE_POINT_OBSERVATION",
                probes=observations,
                limitations=[
                    "Reachable bulletin is not a verified point observation feed",
                    "No spatial interpolation or EC conversion performed",
                    "MRC access error is local evidence, not proof the service is globally offline",
                ],
            ),
        )


if __name__ == "__main__":
    main()
