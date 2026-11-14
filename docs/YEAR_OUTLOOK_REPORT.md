# Năm ENSO và mùa khô — hindcast có kiểm soát

Sinh tự động bởi `scripts/backtest_year_outlook.py` (offline, dữ liệu bundled). Tại mỗi `as_of`, engine chỉ dùng ONI có cửa sổ 3 tháng **đã kết thúc trước tháng của as_of** (15/11 → tháng giữa 09 = ASO) và chỉ các mùa khô đã kết thúc trước as_of. Mỗi ca chạy hai lần: có năm tương tự ENSO (mặc định) và ẩn ONI (engine cũ, mọi năm như nhau). Sau đó so với mưa mùa khô THỰC (tháng 12–4) và mô phỏng lại phương án đứng đầu của mỗi engine trên thời tiết NASA POWER thực. Đây là liên hệ thống kê, **không phải dự báo**.

## 0. Mùa khô 2026–27 cho 4 ruộng demo (as_of 2026-11-14)

| Ruộng | Pha (ONI) | Năm tương tự | Mưa 12–4 tương tự / mọi năm (mm) | r | Top-1 trước (mọi năm như nhau) | Top-1 sau (ENSO) | Shortlist khác? |
|---|---|---|---|---|---|---|---|
| Cần Thơ | EL_NINO_STRONG (2,46) | 2015–16, 2023–24, 2002–03, 2009–10, 2004–05 | 50 / 164 | -0,54 | low_risk rice/maize/rice | low_risk rice/peanut/rice | CÓ |
| Sóc Trăng | EL_NINO_STRONG (2,46) | 2015–16, 2023–24, 2002–03, 2009–10, 2004–05 | 49 / 161 | -0,41 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không |
| Bến Tre | EL_NINO_STRONG (2,46) | 2015–16, 2023–24, 2002–03, 2009–10, 2004–05 | 65 / 162 | -0,48 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | CÓ |
| Châu Đốc | EL_NINO_STRONG (2,46) | 2015–16, 2023–24, 2002–03, 2009–10, 2004–05 | 72 / 234 | -0,71 | low_risk rice/peanut/rice | low_risk rice/peanut/rice | không |

- Cần Thơ: Mùa khô 2026–27: El Niño mạnh (ONI +2,5). Các năm tương tự 2015–16, 2023–24… mưa mùa khô chỉ khoảng 30 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo. (Tín hiệu thống kê, không phải dự báo: tương quan ONI (tháng giữa 09) với mưa tháng 12–4 sau đó r = -0,54 trên 24 năm. Năm 2018–19 cũng El Niño nhưng mưa mùa khô 295 mm. Hindcast: hướng mưa đúng 12/15 ca; chưa cho thấy lợi thế tưới của top-1 (0/15 ca giảm).)
- Sóc Trăng: Mùa khô 2026–27: El Niño mạnh (ONI +2,5). Các năm tương tự 2015–16, 2023–24… mưa mùa khô chỉ khoảng 30 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo. (Tín hiệu thống kê, không phải dự báo: tương quan ONI (tháng giữa 09) với mưa tháng 12–4 sau đó r = -0,41 trên 24 năm. Năm 2018–19 cũng El Niño nhưng mưa mùa khô 228 mm. Hindcast: hướng mưa đúng 12/15 ca; chưa cho thấy lợi thế tưới của top-1 (0/15 ca giảm).)
- Bến Tre: Mùa khô 2026–27: El Niño mạnh (ONI +2,5). Các năm tương tự 2015–16, 2023–24… mưa mùa khô chỉ khoảng 40 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo. (Tín hiệu thống kê, không phải dự báo: tương quan ONI (tháng giữa 09) với mưa tháng 12–4 sau đó r = -0,48 trên 24 năm. Năm 2018–19 cũng El Niño nhưng mưa mùa khô 220 mm. Hindcast: hướng mưa đúng 12/15 ca; chưa cho thấy lợi thế tưới của top-1 (0/15 ca giảm).)
- Châu Đốc: Mùa khô 2026–27: El Niño mạnh (ONI +2,5). Các năm tương tự 2015–16, 2023–24… mưa mùa khô chỉ khoảng 31 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo. (Tín hiệu thống kê, không phải dự báo: tương quan ONI (tháng giữa 09) với mưa tháng 12–4 sau đó r = -0,71 trên 24 năm. Năm 2018–19 cũng El Niño nhưng mưa mùa khô 255 mm. Hindcast: hướng mưa đúng 12/15 ca; chưa cho thấy lợi thế tưới của top-1 (0/15 ca giảm).)

## 1. Tín hiệu: ONI (tháng giữa 09, không nhìn trước) và mưa tháng 12–4 sau đó

| Điểm | r (IMERG) | n | r (POWER) | n |
|---|---|---|---|---|
| Cần Thơ | -0,54 | 24 | -0,48 | 25 |
| Sóc Trăng | -0,41 | 24 | -0,50 | 25 |
| Bến Tre | -0,48 | 24 | -0,51 | 25 |
| Châu Đốc | -0,71 | 24 | -0,44 | 25 |

r âm = ONI càng cao (El Niño) thì mùa khô sau đó càng ít mưa. n ≈ 24 mùa (2001–02…2024–25): tín hiệu đáng kể nhưng nhiều năm lệch.

## 2. Hindcast theo năm

| Điểm | as_of | ONI (tháng 09) | Pha | Năm tương tự | Kỳ vọng mưa 12–4: tương tự / mọi năm (mm) | Mưa thực IMERG / POWER (mm) | Top-1 có ENSO | Top-1 mọi năm như nhau | Shortlist khác? | Tưới thực top-1 ENSO / cũ (mm) |
|---|---|---|---|---|---|---|---|---|---|---|
| Cần Thơ | 2010-11-15 | -1,43 | LA_NINA | TOO_FEW_ANALOG_YEARS | – / – | 174 / 131 | low_risk rice/maize/rice | low_risk rice/maize/rice | không | 1.070 / 1.070 |
| Cần Thơ | 2015-11-15 | 2,02 | EL_NINO_STRONG | 2002–03, 2009–10, 2004–05, 2006–07 | 92 / 134 | 50 / 37 | low_risk rice/maize/rice | low_risk rice/maize/rice | không | 1.310 / 1.310 |
|  | | | | _Mùa khô 2015–16: El Niño mạnh (ONI +2,0). Các năm tương tự 2002–03, 2009–10… mưa mùa khô chỉ khoảng 69 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo._ | | | | | | |
| Cần Thơ | 2018-11-15 | 0,52 | EL_NINO | 2006–07, 2004–05, 2009–10, 2002–03, 2015–16 | 74 / 154 | 295 / 244 | low_risk rice/sesame/rice | low_risk rice/sesame/rice | CÓ | 831 / 831 |
|  | | | | _Mùa khô 2018–19: El Niño (ONI +0,5). Các năm tương tự 2006–07, 2004–05… mưa mùa khô chỉ khoảng 48 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo._ | | | | | | |
| Cần Thơ | 2019-11-15 | 0,31 | NEUTRAL | 2012–13, 2014–15, 2003–04, 2005–06, 2001–02 | 104 / 164 | 51 / 112 | low_risk rice/sesame/rice | low_risk rice/sesame/rice | không | 1.253 / 1.253 |
|  | | | | _Mùa khô 2019–20: ENSO trung tính (ONI +0,3). Các năm tương tự 2012–13, 2014–15… mưa mùa khô chỉ khoảng 63 % năm thường. Tín hiệu thống kê mưa; chưa suy ra nguy cơ mặn. Tín hiệu thống kê, không phải dự báo._ | | | | | | |
| Cần Thơ | 2020-11-15 | -0,77 | LA_NINA | 2011–12, 2007–08, 2010–11 | 188 / 154 | 283 / 279 | low_risk rice/sesame/rice | low_risk rice/sesame/rice | không | 786 / 786 |
|  | | | | _Mùa khô 2020–21: La Niña (ONI -0,8). Các năm tương tự 2011–12, 2007–08… mưa mùa khô gần như năm thường. Tín hiệu thống kê, không phải dự báo._ | | | | | | |
| Cần Thơ | 2023-11-15 | 1,50 | EL_NINO_STRONG | 2015–16, 2002–03, 2009–10, 2004–05, 2006–07 | 74 / 164 | 45 / 47 | low_risk rice/peanut/rice | low_risk rice/maize/rice | CÓ | 1.083 / 1.034 |
|  | | | | _Mùa khô 2023–24: El Niño mạnh (ONI +1,5). Các năm tương tự 2015–16, 2002–03… mưa mùa khô chỉ khoảng 45 % năm thường — nguy cơ hạn, mặn có thể cao hơn bình thường. Tín hiệu thống kê, không phải dự báo._ | | | | | | |
| Sóc Trăng | 2010-11-15 | -1,43 | LA_NINA | TOO_FEW_ANALOG_YEARS | – / – | 165 / 143 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 1.029 / 1.029 |
| Sóc Trăng | 2015-11-15 | 2,02 | EL_NINO_STRONG | 2002–03, 2009–10, 2004–05, 2006–07 | 60 / 115 | 79 / 38 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 1.108 / 1.108 |
| Sóc Trăng | 2018-11-15 | 0,52 | EL_NINO | 2006–07, 2004–05, 2009–10, 2002–03, 2015–16 | 73 / 157 | 228 / 209 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 867 / 867 |
| Sóc Trăng | 2019-11-15 | 0,31 | NEUTRAL | 2012–13, 2014–15, 2003–04, 2005–06, 2001–02 | 70 / 161 | 32 / 84 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 1.180 / 1.180 |
| Sóc Trăng | 2020-11-15 | -0,77 | LA_NINA | 2011–12, 2007–08, 2010–11 | 184 / 157 | 183 / 249 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 905 / 905 |
| Sóc Trăng | 2023-11-15 | 1,50 | EL_NINO_STRONG | 2015–16, 2002–03, 2009–10, 2004–05, 2006–07 | 73 / 161 | 49 / 28 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 1.006 / 1.006 |
| Bến Tre | 2010-11-15 | -1,43 | LA_NINA | TOO_FEW_ANALOG_YEARS | – / – | 158 / 145 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 987 / 987 |
| Bến Tre | 2015-11-15 | 2,02 | EL_NINO_STRONG | 2002–03, 2009–10, 2004–05, 2006–07 | 77 / 119 | 65 / 48 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 1.151 / 1.151 |
| Bến Tre | 2018-11-15 | 0,52 | EL_NINO | 2006–07, 2004–05, 2009–10, 2002–03, 2015–16 | 73 / 158 | 220 / 201 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 870 / 870 |
| Bến Tre | 2019-11-15 | 0,31 | NEUTRAL | 2012–13, 2014–15, 2003–04, 2005–06, 2001–02 | 67 / 162 | 35 / 80 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 1.196 / 1.196 |
| Bến Tre | 2020-11-15 | -0,77 | LA_NINA | 2011–12, 2007–08, 2010–11 | 167 / 158 | 244 / 259 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 847 / 847 |
| Bến Tre | 2023-11-15 | 1,50 | EL_NINO_STRONG | 2015–16, 2002–03, 2009–10, 2004–05, 2006–07 | 73 / 162 | 48 / 38 | low_risk rice/fallow_cover/rice | low_risk rice/fallow_cover/rice | không | 998 / 998 |

## 3. Kết luận (số liệu, không tô vẽ)

- Có năm tương tự (status OK): **15/18** ca; còn lại UNAVAILABLE (< 3 năm cùng pha trong các năm lịch sử trước as_of; 2010 chỉ có 2001–2008) → engine y như cũ.
- Hướng mưa (khô/ướt hơn trung vị các năm trước) đúng ở **12/15** ca OK.
- Các ca trật: Cần Thơ 2018–19: kỳ vọng khô hơn thường (tương tự 74 mm, mọi năm 154 mm), thực 295 mm; Sóc Trăng 2018–19: kỳ vọng khô hơn thường (tương tự 73 mm, mọi năm 157 mm), thực 228 mm; Bến Tre 2018–19: kỳ vọng khô hơn thường (tương tự 73 mm, mọi năm 158 mm), thực 220 mm.
- Shortlist khác engine cũ ở **2/15** ca OK. Tưới thực của phương án đứng đầu (cùng mô hình FAO-56, thời tiết POWER thực): ENSO ít hơn ở 0 ca, nhiều hơn ở 1 ca, bằng ở 14 ca. Lưu ý top-1 là chiến lược `low_risk` (theo ưu tiên mặc định), không phải chiến lược tiết kiệm nước, nên tưới thực không phải thước đo duy nhất.
- 2019: ONI ASO 2019 = +0,31 (trung tính) dù SON/OND sau đó lên El Niño yếu; quy tắc không nhìn trước nên engine KHÔNG gọi 2019–20 là năm El Niño. Năm 2018–19 là El Niño yếu (ASO +0,52) nhưng mùa khô mưa nhiều — ca trật điển hình.

## 4. Hạn chế

- ONI là chỉ số NOAA (không phải NASA); NOAA hiệu chỉnh lại giá trị cũ (ERSST phiên bản mới), file bundled là bản 2026, nên giá trị quá khứ có thể khác chút so với bản công bố tại thời điểm đó.
- Liên hệ thống kê với ~24 mùa khô; năm tương tự không phải dự báo, không có xác suất hiệu chỉnh.
- Mưa IMERG/POWER là ô lưới (11 km / 50 km), không phải đo tại ruộng; không có quan trắc mặn nên không chấm được rủi ro mặn thật.
- Hindcast trước 2026 giữ khung mặn nhiều năm. Kế hoạch 2026–27 chỉ dời khung khi có thêm bản tin SIWRR (qua báo); ENSO riêng lẻ không dời mùa mặn.
- Hindcast trước ~2012 có ít năm lịch sử (dữ liệu từ 2001), nên thường UNAVAILABLE.

