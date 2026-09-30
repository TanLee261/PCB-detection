# Môi Trường Và Phần Cứng

Ghi nhận ngày 2026-09-16 trong quá trình thiết lập môi trường Tuần 1.

| Hạng mục | Giá trị |
| --- | --- |
| Hệ điều hành | macOS 15.7 (build 24G222) |
| Máy tính | MacBook Pro (MacBookPro18,1, MK1E3LL/A) |
| CPU | Apple M1 Pro, 10 cores (8 performance, 2 efficiency) |
| GPU | Apple M1 Pro, GPU tích hợp 16 lõi, Metal 3 |
| Bộ nhớ GPU | Dùng chung bộ nhớ hệ thống; macOS không báo cáo VRAM chuyên dụng riêng biệt |
| RAM | 16 GB (17,179,869,184 bytes) |
| Python | 3.13.5 |
| PyTorch | 2.14.0 |
| Torchvision | 0.29.0 |
| Ultralytics | 8.4.153 |
| Phiên bản CUDA | Không có |
| CUDA khả dụng | Không |
| Apple MPS khả dụng | Có |

Môi trường dự án nằm tại `.venv/`. Kích hoạt bằng lệnh `source .venv/bin/activate`.

## Yêu Cầu Đo Latency

Khi báo cáo latency, phải nêu model CPU, model GPU và VRAM, RAM, hệ điều hành, phiên bản CUDA, PyTorch và Ultralytics. Kết quả latency cuối cùng phải được đo trên cùng máy có cấu hình phần cứng và phần mềm đã nêu ở trên.
