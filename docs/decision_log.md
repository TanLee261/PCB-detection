# Nhật Ký Quyết Định

## 2026-09-17: Cấu Hình Huấn Luyện Baseline Cố Định

- Quyết định: Dùng `yolov8n.pt` làm model baseline.
- Lý do: Model nhỏ gọn, phù hợp làm mốc huấn luyện nhanh và có thể tái lập cho các thí nghiệm tiếp theo.
- Quyết định: Cố định `imgsz` là 640.
- Lý do: Lỗi PCB là các vật thể nhỏ. Ảnh đầu vào 640 px giữ được nhiều chi tiết lỗi hơn; giảm kích thước ảnh có thể làm giảm trực tiếp hiệu quả phát hiện vật thể nhỏ.
- Quyết định: Cố định 100 epochs, batch size 16, `optimizer: auto`, seed 42 và patience 30.
- Lý do: Cấu hình cố định giúp các thí nghiệm có thể so sánh và tái lập.
- Quyết định: Dùng tỷ lệ train/validation/test là 70/15/15 với sáu lớp lỗi: `missing_hole`, `mouse_bite`, `open_circuit`, `short`, `spur` và `spurious_copper`.
- Lý do: Tỷ lệ này dành riêng tập validation và test độc lập, đồng thời giữ phần lớn dữ liệu cho huấn luyện.

Cấu hình baseline cố định được lưu tại `configs/base.yaml`.

## 2026-09-17: Ghi Nhận Môi Trường

- Quyết định: Ghi nhận phiên bản phần cứng và phần mềm tại `docs/hardware.md`.
- Lý do: Kết quả huấn luyện và latency phải có thể tái lập, đồng thời được đánh giá theo đúng cấu hình máy đã tạo ra kết quả đó.

## 2026-09-17: Phân Bin Kích Thước Bounding Box Tuần 3

- Quyết định: Cố định các bin COCO tại `imgsz=640`: nhỏ khi `area_px < 32^2 = 1024`; trung bình khi `32^2 = 1024 <= area_px <= 96^2 = 9216`; lớn khi `area_px > 96^2 = 9216`.
- Lý do: Ngưỡng COCO chỉ có ý nghĩa khi diện tích box được đo trên không gian đầu vào cố định. Vì vậy, notebook scale giữ tỷ lệ mỗi ảnh PKU vào canvas `640 x 640` bằng `gain = min(640 / W, 640 / H)` trước khi tính `w_px`, `h_px` và `area_px`; padding letterbox không làm thay đổi kích thước box.
- Git commit: `chưa commit`.

## 2026-09-19: Quyết Định Khóa Split Tuần 4 và Chống Rò Rỉ Dữ Liệu (Anti-Leakage)

- Quyết định: Chọn `PKU-Market-PCB` là dataset chính duy nhất cho quy trình huấn luyện/đánh giá; chuẩn hóa toàn bộ nhãn về định dạng YOLO format lưu tại `data/processed/labels/`.
- Lý do: Kết quả đối chiếu tương thích tại `scripts/06_dataset_compare.ipynb` cho thấy DeepPCB không đạt 5/5 tiêu chí tương thích về miền ảnh, phân bố kích thước và ontology nhãn.
- Quyết định: Sử dụng `GroupShuffleSplit` chia tập dữ liệu theo `group_id` (PCB board prefix) với tỷ lệ `split_ratio: [0.7, 0.15, 0.15]`.
- Quyết định điều chỉnh Seed: Chọn và cố định vĩnh viễn `seed: 41` trong `configs/base.yaml`.
- Lý do điều chỉnh Seed: Với `seed: 42`, các board mạch `01`, `04`, `05`, `06`, `07` bị tách vào các split khác nhau, dẫn tới 40 cặp ảnh có khoảng cách Hamming pHash $\le 5$ (độ tương đồng đặc trưng cao) bị rò rỉ xuyên split. Chuyển sang `seed: 41` giúp gom toàn bộ thành phần liên thông này vào tập Train, triệt tiêu 100% rò rỉ pHash xuyên split (0 cặp vi phạm), đồng thời phân bố 6 lớp lỗi giữa các split đạt độ cân bằng cao.
- Khóa phân vùng: Đã xác thực không rò rỉ và khóa cố định bằng mã MD5 checksum tại `data/splits/split_manifest.json` và xuất báo cáo `results/leakage_report.txt` (toàn bộ PASS). Từ thời điểm này trở đi, không thay đổi phân vùng dữ liệu.


## 2026-09-22: Kết Quả Smoke Test Baseline B0 (Tuần 5)

- Quyết định: Hoàn tất kiểm thử pipeline huấn luyện end-to-end cho Baseline B0 với smoke subset 50 ảnh.
- Smoke Test Config: model=yolov8n.pt, imgsz=320, batch=8, epochs=3, subset=40 train / 10 val (0 test).
- Augmentation Recipe Đã Khóa: degrees=0.0, shear=0.0, perspective=0.0, flipud=0.0 (chống biến dạng hình học PCB); fliplr=0.5, mosaic=1.0, scale=0.5, translate=0.1.
- Kết quả Smoke Test: PASS toàn bộ 6 điều kiện (loss không NaN, nhận đủ 6 class, sinh đủ weights/best.pt, chạy thành công model.val() và model.predict()).
- Đo lường chi phí: 7.47 s/epoch (subset 40 ảnh); ước tính tập đầy đủ 150 epochs mất ~31.0 giờ trên cấu hình máy hiện tại.

## 2026-09-22: Kết Quả Smoke Test Baseline B0 (Tuần 5)

- Quyết định: Hoàn tất kiểm thử pipeline huấn luyện end-to-end cho Baseline B0 với smoke subset 50 ảnh.
- Smoke subset 50 ảnh: 40 ảnh train, 10 ảnh val; tuyệt đối không dùng test set (0 ảnh từ test.txt).
- Smoke Test Config: model=yolov8n.pt, imgsz=320, batch=8, epochs=3, seed=41.
- Augmentation Recipe: degrees=0.0, shear=0.0, perspective=0.0, flipud=0.0 (chống biến dạng hình học PCB); fliplr=0.5, mosaic=1.0, scale=0.5, translate=0.1, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4.
- Kết quả PASS/FAIL: PASS toàn bộ 8/8 tiêu chuẩn kỹ thuật (loss không NaN, nhận đủ 6 class, sinh đủ weights/best.pt, val và predict thành công).
- Thời gian/epoch: 7.33 s/epoch (subset 40 ảnh); ước tính tập đầy đủ 150 epochs mất ~30.4 giờ trên cấu hình CPU hiện tại.
- Ràng buộc kiểm chứng: Tuyệt đối không dùng test set và không tune threshold trong giai đoạn smoke test.

## 2026-09-22: Kết Quả Smoke Test Baseline B0 (Tuần 5)

- Quyết định: Hoàn tất kiểm thử pipeline huấn luyện end-to-end cho Baseline B0 với smoke subset 50 ảnh.
- Smoke subset 50 ảnh: 40 ảnh train, 10 ảnh val; tuyệt đối không dùng test set (0 ảnh từ test.txt).
- Smoke Test Config: model=yolov8n.pt, imgsz=320, batch=8, epochs=3, seed=41.
- Augmentation Recipe: degrees=0.0, shear=0.0, perspective=0.0, flipud=0.0 (chống biến dạng hình học PCB); fliplr=0.5, mosaic=1.0, scale=0.5, translate=0.1, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4.
- Kết quả PASS/FAIL: PASS toàn bộ 6/6 tiêu chuẩn kỹ thuật Tuần 5 (loss không NaN, nhận đủ 6 class, sinh đủ weights/best.pt, val và predict thành công có ảnh vẽ box).
- Đo lường chi phí: duration_seconds=21.14s, seconds_per_epoch=7.05s (subset 40 ảnh); ước tính tập đầy đủ 150 epochs mất ~29.3 giờ trên CPU.
- Ràng buộc kiểm chứng: Tuyệt đối không dùng test set, không tune threshold, không làm B1/B2/Proposed.
- Đề xuất tối ưu Epoch Budget (>20 giờ): Ước tính full train 150 epochs trên CPU mất ~29.3 giờ (>20h). Đề xuất hai phương án cần quyết định: (1) Giảm epoch budget xuống 70-80 epochs kèm early stopping (patience=15-20); (2) Chuyển môi trường huấn luyện sang GPU (Google Colab T4 / Kaggle GPU) để chạy 150 epochs dưới 2 giờ. Cần quyết định trước khi chạy B0 full train.

## 2026-09-22: Điều Chỉnh Epoch Budget Baseline B0 Xuống 20 Epochs (Tuần 6)

- Quyết định: Điều chỉnh giảm số lượng epoch huấn luyện Baseline B0 (`epochs`) từ 100 epochs xuống 20 epochs trong `configs/base.yaml` và `scripts/11_train_B0_full.ipynb`.
- Lý do kỹ thuật:
  - Tập huấn luyện đầy đủ gồm 3,989 ảnh (với `batch: 16` tương đương ~250 iterations/epoch). Với 20 epochs, mô hình thực hiện khoảng 5,000 bước cập nhật gradient, đủ để hoàn tất quá trình làm ấm (warmup), hội tụ loss và đánh giá đầy đủ năng lực nhận diện của Baseline YOLOv8n trên 6 lớp khuyết tật PCB.
  - Tối ưu hóa thời gian huấn luyện thực nghiệm: Rút ngắn thời gian chạy thực tế xuống còn ~10-15 phút trên GPU (Kaggle/Colab) hoặc ~3-4 giờ trên CPU.
  - Giữ nguyên tính nhất quán của hệ thống: Cố định toàn bộ các siêu tham số cốt lõi khác (`imgsz: 640`, `batch: 16`, `seed: 41`, `optimizer: auto`, `patience: 30`) và Augmentation Recipe đã khóa cho PCB (`degrees: 0.0`, `shear: 0.0`, `perspective: 0.0`, `flipud: 0.0`, `fliplr: 0.5`).


## 2026-09-23: Huấn Luyện Thành Công Baseline B0 (YOLOv8n Full Train)

- Quyết định: Hoàn tất huấn luyện mô hình Baseline B0 chuẩn làm mốc đối sánh (benchmark gốc).
- Cấu hình: model=yolov8n.pt, imgsz=640, epochs=20, batch=16, optimizer=auto, patience=30.
- Seed đã khóa: 41.
- Split Checksum (MD5): train=12fffda36e6850eb2912fa0d0a18c494, val=9246d70f17bf0527d4676d9fee31c347, test=9ea1136e12040e92526038415312ab37.
- Augmentation Recipe: degrees=0.0, shear=0.0, perspective=0.0, flipud=0.0, fliplr=0.5, mosaic=1.0, scale=0.5, translate=0.1, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4.
- Thời lượng huấn luyện (duration): 31877.73 s (~8.85 giờ).
- Checkpoint: best checkpoint lưu tại `runs/B0/weights/best.pt` (Epoch tốt nhất: 15, val mAP@0.5: 0.6755, mAP@0.5:0.95: 0.2406).
- Ràng buộc kiểm chứng: Tuyệt đối không sử dụng tập test (`data/splits/test.txt`) để tuning bất kỳ siêu tham số nào.

## 2026-09-23: Chốt Danh Mục Lỗi Chí Mạng (Critical Classes) Cho Đánh Giá B0

- Quyết định: Xác định 2 lớp lỗi chí mạng cần đặc biệt theo dõi và giảm thiểu False Negative: `critical_classes = ["open_circuit", "short"]`.
- Lý do kỹ thuật: `open_circuit` gây hở mạch/mất tín hiệu hoàn toàn; `short` gây chập nguồn/cháy nổ bo mạch. Bỏ sót 2 lỗi này dẫn đến rủi ro hư hỏng nghiêm trọng cho thiết bị điện tử.
- Ứng dụng: Dùng làm tiêu chí cốt lõi để tính Critical False Negative Rate và thiết lập hàm chi phí phạt trong giai đoạn B2 và Proposed.

## 2026-09-23: Kiểm Chứng Kiến Trúc B1 (YOLOv8n + P2) và Kết Quả Smoke Test (Tuần 7)

- Quyết định: Hoàn tất kiểm chứng kiến trúc B1 (YOLOv8n-P2) và chạy thử nghiệm smoke 2 epoch thành công.
- So sánh Chi phí Kiến trúc B0 vs B1:
  - B0 (YOLOv8n)   : 3,012,018 parameters, 8.20 GFLOPs, checkpoint: 5.94 MB.
  - B1 (YOLOv8n-P2): 2,927,352 parameters, 12.36 GFLOPs, checkpoint: 5.99 MB.
  - Biến động tương đối: Tham số thay đổi -2.81%, GFLOPs tăng +50.83% do bổ sung tầng đặc trưng độ phân giải cao 160x160 (stride 4).
- Forward Shape Check: PASS 4/4 mức phân giải Detect Head: P2 (160x160, stride 4), P3 (80x80, stride 8), P4 (40x40, stride 16), P5 (20x20, stride 32).
- Smoke Test 2 Epochs: PASS toàn bộ tiêu chuẩn kỹ thuật (không NaN loss, không shape mismatch, checkpoint lưu tại `runs/smoke_B1_P2/weights/best.pt`).
- Ràng buộc kiểm chứng: Mô hình B1 **chỉ thay đổi duy nhất biến kiến trúc (thêm tầng P2)**; giữ nguyên 100% split dữ liệu (`seed: 41`), Augmentation Recipe của PCB, loss function và nguyên tắc không tuning trên test set.

## 2026-09-24: Huấn Luyện Thành Công Mô Hình B1 (YOLOv8n + P2 Full Train)

- Quyết định: Hoàn tất huấn luyện mô hình B1 (YOLOv8n-P2) phục vụ đánh giá năng lực phát hiện khuyết tật vi mô so với Baseline B0.
- Cấu hình huấn luyện: model=configs/yolov8n-p2.yaml, pretrained=yolov8n.pt, imgsz=640, epochs=20, batch=16, optimizer=auto, patience=30.
- Seed đã khóa: 41.
- Split Checksum (MD5): train=unknown, val=unknown, test=unknown.
- Augmentation Recipe: degrees=0.0, shear=0.0, perspective=0.0, flipud=0.0, fliplr=0.5, mosaic=1.0, scale=0.5, translate=0.1, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4.
- Thời lượng huấn luyện: 53252.37 s (~14.79 giờ).
- Checkpoint tốt nhất: `runs/B1/weights/best.pt` (val mAP@0.5: 0.6812, mAP@0.5:0.95: 0.2728).
- Ràng buộc kiểm chứng: Mô hình B1 **chỉ thay đổi duy nhất biến kiến trúc P2**; tuyệt đối không sử dụng tập test (`data/splits/test.txt`) để tuning bất kỳ siêu tham số nào.

## 2026-09-24: Đánh Giá Mô Hình B1 (YOLOv8n + P2) và Đối Sánh Hiệu Năng Với B0 (Tuần 8)

- Quyết định: Hoàn tất đánh giá toàn diện mô hình B1 trên validation set (368 ảnh) và xuất bảng đối sánh hiệu năng với Baseline B0.
- Bảng Đối Sánh B0 vs B1 (Validation):
| config   |   mAP@0.5 |   mAP@0.5:0.95 |   recall_small |   recall_medium |   recall_large |   recall_open_circuit |   recall_short | params         | GFLOPs         |
|:---------|----------:|---------------:|---------------:|----------------:|---------------:|----------------------:|---------------:|:---------------|:---------------|
| B0       |    0.6451 |         0.2693 |         0.5917 |          0.2793 |              0 |                0.5993 |         0.6185 | 3012018        | 8.2            |
| B1_P2    |    0.6812 |         0.2728 |         0.6682 |          0.5    |              0 |                0.571  |         0.6945 | 2927352        | 12.36          |
| Delta    |    0.0362 |         0.0036 |         0.0765 |          0.2207 |              0 |               -0.0283 |         0.076  | -84666 (-2.8%) | +4.16 (+50.7%) |
- Nhận định sơ bộ (Validation):
  - mAP@0.5: B0 = 0.6451, B1 = 0.6812 (Chênh lệch: +0.0362).
  - Recall Small: B0 = 59.17%, B1 = 66.82% (Chênh lệch: +7.65%).
  - Đánh đổi chi phí: GFLOPs tăng từ 8.20 lên 12.36 (+50.7%).
- Ràng buộc kiểm chứng: Toàn bộ quá trình đánh giá chỉ thực hiện trên tập `val.txt`; tuyệt đối **không sử dụng tập test (`data/splits/test.txt`) để tuning** hay lựa chọn mô hình.

## 2026-09-24: Chốt Danh Mục Lỗi Chí Mạng (Critical Classes) Cho Đánh Giá B0

- Quyết định: Xác định 2 lớp lỗi chí mạng cần đặc biệt theo dõi và giảm thiểu False Negative: `critical_classes = ["open_circuit", "short"]`.
- Lý do kỹ thuật: `open_circuit` gây hở mạch/mất tín hiệu hoàn toàn; `short` gây chập nguồn/cháy nổ bo mạch. Bỏ sót 2 lỗi này dẫn đến rủi ro hư hỏng nghiêm trọng cho thiết bị điện tử.
- Ứng dụng: Dùng làm tiêu chí cốt lõi để tính Critical False Negative Rate và thiết lập hàm chi phí phạt trong giai đoạn B2 và Proposed.

## 2026-09-24: Hoàn Tất Huấn Luyện Baseline B0 100 Epochs (Kaggle GPU) và Đánh Giá Toàn Diện

- Quyết định: Hoàn tất huấn luyện Baseline B0 đầy đủ 100 epochs trên môi trường GPU (Kaggle Dual Tesla T4), giải quyết triệt để hạn chế tài nguyên/thời gian khi chạy 20 epochs trên CPU cục bộ.
- Cấu hình huấn luyện: model=yolov8n.pt, imgsz=640, epochs=100, batch=16, seed=41, patience=30.
- Kết quả huấn luyện: Early stopping dừng ở epoch 71 (tổng thời gian 162.74 phút ~ 2.7 giờ trên Tesla T4).
- Checkpoint: `runs/B0_100ep/weights/best.pt` (val mAP@0.5: 0.7614, mAP@0.5:0.95: 0.3150).
- Đánh giá trên Validation set 368 ảnh (`scripts/12_eval_B0.ipynb`):
  - **mAP@0.5**: Tăng từ `0.6451` (20ep) lên `0.7471` (+10.20%).
  - **mAP@0.5:0.95**: Tăng từ `0.2693` lên `0.3018` (+3.25%).
  - **Mean Precision**: `0.8047`; **Mean Recall**: `0.6853`.
  - **Small Defect Recall**: Tăng từ `59.17%` lên `74.65%` (+15.48%).
  - **Critical Defect Recall (open_circuit + short)**: Tăng từ `47.93%` lên `75.48%` (+27.55%).
  - **Critical False Negative Rate**: Giảm mạnh từ `52.07%` xuống `24.52%` (giảm hơn một nửa tỷ lệ sót lỗi chí mạng).
  - **Board-Level False Accept Rate (Escape Rate)**: Giảm từ `3.80%` (14 bo mạch lọt) xuống `0.00%` (0 bo mạch bị bỏ lọt).
- Bảo toàn dữ liệu: Kết quả 20 epochs trước đó được sao lưu tại `results/B0_20ep/`. Tập `test.txt` tiếp tục được cô lập 100%.


## 2026-09-25: Đánh Giá Mô Hình B1 (YOLOv8n + P2) và Đối Sánh Hiệu Năng Với B0 (Tuần 8)

- Quyết định: Hoàn tất đánh giá toàn diện mô hình B1 trên validation set (368 ảnh) và xuất bảng đối sánh hiệu năng với Baseline B0.
- Bảng Đối Sánh B0 vs B1 (Validation):
| config   |   mAP@0.5 |   mAP@0.5:0.95 |   recall_small |   recall_medium |   recall_large |   recall_open_circuit |   recall_short | params         | GFLOPs         |
|:---------|----------:|---------------:|---------------:|----------------:|---------------:|----------------------:|---------------:|:---------------|:---------------|
| B0       |    0.7471 |         0.3018 |         0.7465 |          0.7    |              0 |                0.6883 |         0.7007 | 3012018        | 8.2            |
| B1_P2    |    0.7034 |         0.2832 |         0.6535 |          0.5207 |              0 |                0.6464 |         0.7059 | 2927352        | 12.36          |
| Delta    |   -0.0437 |        -0.0186 |        -0.093  |         -0.1793 |              0 |               -0.0419 |         0.0052 | -84666 (-2.8%) | +4.16 (+50.7%) |
- Nhận định sơ bộ (Validation):
  - mAP@0.5: B0 = 0.7471, B1 = 0.7034 (Chênh lệch: -0.0437).
  - Recall Small: B0 = 74.65%, B1 = 65.35% (Chênh lệch: -9.30%).
  - Đánh đổi chi phí: GFLOPs tăng từ 8.20 lên 12.36 (+50.7%).
- Ràng buộc kiểm chứng: Toàn bộ quá trình đánh giá chỉ thực hiện trên tập `val.txt`; tuyệt đối **không sử dụng tập test (`data/splits/test.txt`) để tuning** hay lựa chọn mô hình.

## 2026-09-25: Khóa Quy Tắc Threshold Giai Đoạn 5

- **Quyết định**: Khóa chính thức quy tắc lựa chọn ngưỡng và giá trị ngưỡng tin cậy ($\tau$) cho Baseline B0 và Model B1 trên tập kiểm định (Validation set).
- **Quy tắc được chọn (`selected_rule`)**: `max_f2`
  - *Hệ số cân bằng*: $\beta = 2$ (phạt nặng False Negative, ưu tiên bảo vệ tính toàn vẹn của mạch điện tử).
  - *Lý do*: Quy tắc ứng viên Recall-Target ($R_{target} = 0.95$) không khả thi trên tập validation do độ nhạy cực đại của B0 chỉ đạt $86.62\%$ và B1 đạt $79.78\%$ (ngay cả tại mức sàn $conf = 0.01$).
- **Lớp lỗi chí mạng (`critical_classes`)**: `open_circuit`, `short` (hai lỗi gây mất tín hiệu hoặc chập cháy nguy hiểm nhất).
- **Ngưỡng tối ưu đã khóa**:
  - **$\tau_{B0} = 0.20$** ($F_2 = 0.7283$, Precision = 0.6356, Recall = 0.7559, Critical Recall = 76.91%, Critical FN Rate = 23.09%, Board FAR = 0.00%).
  - **$\tau_{B1} = 0.13$** ($F_2 = 0.6460$, Precision = 0.4755, Recall = 0.7097, Critical Recall = 70.06%, Critical FN Rate = 29.94%, Board FAR = 0.00%).
  - *Tính độc lập*: Hai mô hình sử dụng hai ngưỡng riêng biệt phản ánh sự khác biệt về đặc tính phân giải của Detect Head (B0 dùng 3 đầu P3-P5; B1 thêm đầu P2 phân giải cao).
- **Môi trường & Ràng buộc đánh giá**:
  - Toàn bộ quá trình quét lưới 95 ngưỡng và lựa chọn $\tau$ được thực hiện **hoàn toàn trên tập Validation (`data/splits/val.txt` - 368 ảnh)**.
  - **Tập kiểm thử (`data/splits/test.txt` - 480 ảnh) tuyệt đối chưa được sử dụng**, được cô lập $100\%$ và chỉ mở khóa tại Tuần 10 sau khi ngưỡng đã được khóa bất biến.
- **Tệp dữ liệu quét ngưỡng**: `results/threshold_sweep_val.csv` (190 dòng dữ liệu).
- **Danh sách 3 biểu đồ chuẩn hóa**:
  1. `results/threshold_precision_recall_vs_conf.png`: Biến thiên Precision & Recall theo confidence threshold cho B0 và B1.
  2. `results/threshold_f2_vs_conf.png`: Biến thiên $F_2$-Score và điểm cực đại $\tau_{B0} = 0.20, \tau_{B1} = 0.13$.
  3. `results/threshold_board_fa_fr_vs_conf.png`: Tỷ lệ lọt bo mạch lỗi ($Board\ False\ Accept\ Rate$) và vùng an toàn tuyệt đối ($conf \le 0.35$).
- **Giới hạn kỹ thuật ghi nhận (Limitation)**: Do toàn bộ 368 ảnh trong tập validation của dataset PKU-Market-PCB đều chứa khuyết tật (0 bo mạch lành lặn), mẫu số tính $False\ Reject\ Rate$ bằng 0 nên chỉ số này được định nghĩa là `null` (N/A). Hệ thống sử dụng $Board\ False\ Accept\ Rate$ làm tiêu chí an toàn cấp hệ thống.
- **Tệp cấu hình khóa**: `configs/threshold.yaml`.
