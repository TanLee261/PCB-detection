# Phạm Vi, Quy Trình Đánh Giá Và Giới Hạn

## Phạm vi nghiên cứu

Dự án nghiên cứu phát hiện sáu loại khuyết tật bề mặt PCB trên benchmark PKU-Market-PCB: `missing_hole`, `mouse_bite`, `open_circuit`, `short`, `spur` và `spurious_copper`. Đây là prototype nghiên cứu và dashboard minh họa cục bộ, không phải hệ thống AOI sản xuất đã được xác nhận.

PKU-Market-PCB là dataset duy nhất được dùng để train, validation và test. DeepPCB đã được đánh giá tương thích và không được gộp vào pipeline chính; dự án không có kết quả external-domain evaluation, vì vậy không khẳng định khả năng tổng quát hóa sang dataset hoặc dây chuyền khác.

## Thiết kế thí nghiệm

Hai đóng góp cốt lõi được đánh giá bằng bốn cấu hình:

| Cấu hình | Kiến trúc | Ngưỡng | Biến thay đổi |
| --- | --- | --- | --- |
| B0 | YOLOv8n P3-P5 | 0.25 | Baseline |
| B1 | YOLOv8n-P2 P2-P5 | 0.25 | FPN-P2 stride 4 |
| B2 | YOLOv8n P3-P5 | 0.20 | Ngưỡng F2-Max trên trọng số B0 |
| Proposed | YOLOv8n-P2 P2-P5 | 0.13 | FPN-P2 và ngưỡng F2-Max trên trọng số B1 |

Core contribution A là FPN-P2, không phải SAHI. Core contribution B là chọn ngưỡng nhạy cảm chi phí bằng `max_f2` với `beta=2`, được chọn trên validation. Recall target 95% đã được xem xét nhưng không khả thi trên validation; vì vậy dự án không claim tối ưu theo Recall target. Attention module, SAHI và targeted augmentation không được triển khai như contribution độc lập.

Ngưỡng được chọn trên validation rồi khóa trước test. B0/B1 dùng ngưỡng mặc định 0.25; B2 dùng tau B0 = 0.20 và Proposed dùng tau B1 = 0.13. Tập test chỉ phục vụ đánh giá cuối cùng.

## Dataset, split và kích thước lỗi

Split dùng GroupShuffleSplit, seed 41, với 10 group suy ra từ tiền tố tên tệp và kiểm tra pHash. Tỷ lệ mục tiêu là 70/15/15, nhưng tỷ lệ ảnh đã khóa thực tế là 3,989/368/480 trên 4,837 ảnh, tương đương 82.47%/7.61%/9.92%. Sự khác biệt này xuất phát từ ràng buộc chia theo group; báo cáo phải dùng tỷ lệ thực tế thay vì gọi split là 70/15/15.

Kích thước defect được xác định hoàn toàn theo pixel trong không gian input 640: `small` khi `area_px < 1024`, `medium` khi từ 1024 đến 9216, và `large` khi lớn hơn 9216. Không có hiệu chuẩn pixel-to-mm hoặc pixel-to-micromet, nên không diễn giải kích thước theo đơn vị vật lý.

Tỷ lệ small phụ thuộc tập dữ liệu được nêu rõ:

- Toàn dataset audit: 18,372/19,003 box, tương đương 96.68%.
- Test locked: 2,400/2,412 ground-truth box, tương đương 99.50%.
- 99.67% (610/612) là tỷ lệ false negative của Proposed thuộc bin small, không phải Recall phát hiện lỗi small.

## Metrics và giới hạn diễn giải

`Board_FA` là tỷ lệ board có defect bị kết luận PASS vì không còn detection sau threshold. Proposed đạt 0.42% (2/480) trên test. `Board_FR` là N/A vì validation và test không có board defect-free; do đó không thể kết luận specificity, false alarm hoặc tỷ lệ loại bỏ nhầm board tốt.

`PASS` trong dashboard nghĩa là không có detection vượt ngưỡng khóa. Nó không chứng minh board đạt kiểm định điện hoặc đạt chất lượng sản xuất.

Kết quả B0/B1/Proposed dựa trên một seed (41). Kết luận về P2 cần báo cả trade-off: Proposed cải thiện `R_small` và `R_critical`, nhưng mAP@0.5 là 65.41% so với 66.73% của B0/B2.

## Latency và tái lập

Latency chính thức là `results/csv/latency_summary.csv`: Apple M1 Pro/MPS, batch 1, input 640, 20 warmup và 100 lần đo. Cần báo cả mean và p95; không dùng mean dưới 100 ms để claim mọi lần suy luận dưới 100 ms hoặc hệ thống đáp ứng target công nghiệp.

Artifact `results/csv/dataset_statistics.csv` là inventory cũ với số cặp ảnh-nhãn khác thống kê split hiện hành. Không dùng artifact này làm nguồn box count của báo cáo cuối; dùng split manifest, `size_distribution_statistics.csv` và test ground truth đã khóa.
