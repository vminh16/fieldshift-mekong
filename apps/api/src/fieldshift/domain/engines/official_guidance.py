"""Dated regional advice, separate from the ENSO statistical signal."""

import datetime as dt

OFFICIAL_URL = "https://storage-vnportal.vnpt.vn/cmu-khdn/5342/Vanban/2026.6.19-cv-chi-dao-sx-trong-trot-ung-pho-elnino-2026_-_nqmanh_19062026180253__19062026180725_signed.pdf"
SIWRR_PRESS_URL = "https://tienphong.vn/khuyen-cao-mien-tay-ung-pho-han-man-gay-gat-mua-kho-sap-toi-post1882122.tpo"
SIWRR_2026_ONSET_ADVANCE_DAYS = 45  # Jan 15 -> Dec 1; team discretisation, not a field forecast


def evidence(as_of):
    out = {}
    if as_of >= dt.date(2026, 6, 19):
        out["ev_official_2504"] = {
            "kind": "OFFICIAL_GUIDANCE",
            "source": "Cục Trồng trọt và BVTV, Công văn 2504/TTTV-TTBVTV, 19/6/2026",
            "url": OFFICIAL_URL,
            "status": "VERIFIED_PRIMARY_PDF",
            "verified_at": "2026-11-14",
            "summary_vi": "Vùng thiếu nước hoặc 3 vụ kém hiệu quả: cân nhắc 2 vụ hay chuyển một phần sang ngô, vừng, rau đậu; không vượt khả năng cấp nước.",
            "calendar_2026": {
                "early": ["2026-10-10", "2026-10-30"],
                "dot_1": ["2026-11-01", "2026-11-30"],
                "dot_2": ["2026-12-01", "2026-12-31"],
            },
            "limitations": ["Chỉ đạo vùng, không xác nhận an toàn hay tính phù hợp của từng thửa."],
        }
    if as_of >= dt.date(2026, 10, 5):
        out["ev_siwrr_2026_press"] = {
            "kind": "ASSUMPTION",
            "source": "Viện KHTL miền Nam (SIWRR), qua Tiền Phong 05/10/2026",
            "url": SIWRR_PRESS_URL,
            "status": "PRESS_REPORT_ONLY",
            "verified_at": "2026-11-14",
            "summary_vi": "Báo dẫn SIWRR: mặn có thể xuất hiện từ tháng 12/2026; mạnh trong tháng 1 đến đầu tháng 3/2027.",
            "limitations": [
                "Chỉ đọc báo dẫn SIWRR, chưa đọc bản tin gốc; chọn 01/12 là giả định của nhóm, không phải ngày mặn tại thửa."
            ],
        }
    return out


def active_region(region, outlook, as_of, ledger):
    enso = outlook.get("enso") or {}
    if (
        outlook["status"] == "OK"
        and enso.get("phase", "").startswith("EL_NINO")
        and dt.date(2026, 10, 5) <= as_of <= dt.date(2027, 4, 30)
        and "ev_siwrr_2026_press" in ledger
    ):
        return {
            **region,
            "salinity_season": {
                **region["salinity_season"],
                "onset_advance_days": SIWRR_2026_ONSET_ADVANCE_DAYS,
                "onset_advance_year": 2027,
            },
        }, True
    return region, False
