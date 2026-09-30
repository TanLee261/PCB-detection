**NHẬN XÉT – GÓP Ý CHỈNH SỬA  
ĐỀ CƯƠNG KHÓA LUẬN TỐT NGHIỆP**

**NGHIÊN CỨU ỨNG DỤNG THỊ GIÁC MÁY TÍNH VÀ TRÍ TUỆ NHÂN TẠO TRONG KIỂM
ĐỊNH CHẤT LƯỢNG SẢN PHẨM CÔNG NGHIỆP**

# 1. Đánh giá tổng quan

**Kết luận chung:** Đề cương có tính ứng dụng cao và thiết kế thí nghiệm
khá đầy đủ cho bài toán PCB defect detection. Tuy nhiên tên đề tài quá
rộng so với dữ liệu chỉ là PCB; việc ghép DeepPCB + PKU-PCB, đồng thời
tích hợp targeted augmentation + P2 + attention + SAHI tạo quá nhiều
biến và có nguy cơ không còn đối chứng sạch.

**Mức độ khả thi trong 16 tuần:** Khá – 7.5/10 nếu chọn một dataset
chính, một external dataset phụ và giới hạn 2 cải tiến cốt lõi. Nếu bắt
buộc hoàn tất toàn bộ P2+Attention+SAHI+Augmentation+Web/API thì rủi ro
cao.

**Điểm mạnh nổi bật:** Đề cương quan tâm small/tiny defects, FN risk,
group-aware split theo phôi, SAHI/global NMS, per-class recall và
board-level PASS/DEFECTIVE.

**Rủi ro lớn nhất nếu giữ nguyên đề cương:** Việc gộp hai dataset có thể
tạo domain/label mismatch; đồng thời claim công nghiệp như
micromet/real-time chưa được gắn với physical scale và target hardware
cụ thể.

# 2. Điểm mạnh của đề cương hiện tại

-   Xác định đúng small-object problem và nguy cơ mất chi tiết khi
    resize/downsampling.

-   Nhấn mạnh asymmetric error cost và Recall cho open/short circuits,
    phù hợp kiểm định.

-   Có group-aware split để giảm leakage từ cùng phôi PCB.

-   Ablation proposal khá rõ: baseline, augmentation, SAHI, P2,
    attention, full.

-   Có hệ thống metadata, global NMS và board-level decision.

# 3. Các vấn đề cần chỉnh sửa và phản biện chính

| **Mức ưu tiên** | **Vấn đề/nhận xét phản biện**                                                                                                   | **Vì sao cần chỉnh**                                                                                    | **Cách sửa đề xuất**                                                                                                                                                        |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Bắt buộc**    | Tên đề tài nói “sản phẩm công nghiệp” trong khi toàn bộ dataset/method là PCB.                                                  | Tên quá rộng làm phạm vi nghiên cứu không trung thực.                                                   | Đổi thành “... kiểm định khuyết tật bề mặt PCB” hoặc “Phát hiện khuyết tật nhỏ trên PCB bằng YOLO...”                                                                       |
| **Bắt buộc**    | Kế hoạch “đọc và thống nhất nhãn từ DeepPCB và PKU-PCB” chưa chứng minh hai dataset tương thích.                                | Khác domain, annotation protocol, image acquisition hoặc label ontology có thể làm merge trực tiếp sai. | Dùng 01 dataset chính để train/val/test; dataset thứ hai chỉ external test/domain shift nếu thực sự tương thích. Nếu merge, phải có mapping table và distribution analysis. |
| **Bắt buộc**    | Claim “hơn 99% khuyết tật small/very small” và “cấp micromet” chưa được chứng minh bằng thống kê/physical scale trong đề cương. | Dễ bị hội đồng yêu cầu nguồn hoặc dữ liệu đo.                                                           | Chuyển thành giả thuyết/quan sát sẽ kiểm chứng; tính tỷ lệ box theo chuẩn diện tích pixel. Không dùng “micromet” nếu dataset không có pixel-to-mm calibration.              |
| **Cao**         | Có quá nhiều cải tiến đồng thời: targeted augmentation, P2, attention, SAHI.                                                    | Ablation 6 cấu hình cộng tuning từng biến thể vượt ngân sách 16 tuần.                                   | Chọn 2 core contributions: (1) high-resolution/P2 hoặc SAHI, (2) cost-sensitive threshold/recall optimization. Attention hoặc augmentation chỉ phụ.                         |
| **Cao**         | “Targeted Data Augmentation” chưa có định nghĩa và giả thuyết.                                                                  | Không biết augment nhắm lớp hiếm, box nhỏ, lighting hay geometry.                                       | Định nghĩa loại augment, lớp/size nào được áp dụng và mục tiêu metric; không dùng augment có thể phá geometry PCB.                                                          |
| **Cao**         | Group-aware split phụ thuộc có group ID/phôi gốc.                                                                               | Nếu dataset không cung cấp mapping, seed=42 không đủ đảm bảo không leakage.                             | Mô tả cách xác định group: metadata/file naming/template image/hash; kiểm tra không có nhóm trùng giữa splits.                                                              |
| **Cao**         | PASS/DEFECTIVE dùng “confidence threshold” nhưng chưa quy định threshold selection.                                             | Threshold ảnh hưởng trực tiếp false accept/false reject.                                                | Chọn threshold trên validation theo mục tiêu Recall hoặc max Fβ; test khóa. Báo board-level false accept (defect bị pass) và false reject.                                  |
| **Cao**         | FPS/latency “thời gian thực” chưa gắn target hardware và ảnh full resolution.                                                   | SAHI làm số patch thay đổi theo kích thước ảnh nên FPS khung khó so sánh.                               | Định nghĩa target GPU/CPU, input resolution; báo end-to-end latency/full image, patch count, model-only latency riêng.                                                      |
| **Trung bình**  | P2 + attention trên YOLOv8n có thể làm mô hình không còn “n” nhẹ và tăng latency đáng kể.                                       | Trade-off chất lượng–tốc độ là trung tâm đề tài nhưng chưa có budget.                                   | Đặt ràng buộc latency/GFLOPs hoặc maximum model size và chọn variant theo Pareto frontier.                                                                                  |
| **Trung bình**  | Dashboard/API có nhiều chức năng nhưng không đóng góp khoa học chính.                                                           | Dễ tiêu tốn tuần 14–16 trong khi ablation chưa xong.                                                    | Giữ dashboard tối giản upload→boxes→PASS/FAIL; ưu tiên experiments và báo cáo.                                                                                              |

# 4. Nội dung đề xuất thay thế/chỉnh sửa trọng tâm

## 4.1. Tên đề tài đề xuất

“Phát hiện khuyết tật nhỏ trên bề mặt PCB bằng mô hình YOLO cải tiến và
suy luận lát cắt độ phân giải cao”.

## 4.2. Phát biểu vấn đề nghiên cứu nên viết lại

Trong ảnh PCB độ phân giải cao, nghiên cứu đánh giá mức cải thiện Recall
của lỗi nhỏ/critical defects khi áp dụng chiến lược giữ đặc trưng độ
phân giải cao (P2 hoặc SAHI), dưới ràng buộc latency thực tế và split
chống leakage theo phôi.

## 4.3. Câu hỏi nghiên cứu nên chốt

1.  RQ1: Baseline YOLOv8n suy giảm Recall thế nào theo kích thước
    defect?

2.  RQ2: P2 hoặc SAHI cải thiện small-defect Recall/mAP bao nhiêu và làm
    tăng latency bao nhiêu?

3.  RQ3: Kết hợp core improvements có còn lợi khi đánh giá board-level
    false accept/false reject không?

## 4.4. Thiết kế phương pháp/thực nghiệm nên chốt

4.  Chọn 01 dataset chính, group-aware split 70/15/15.

5.  B0 YOLOv8n; B1 + core improvement A; B2 + core improvement B;
    Proposed A+B.

6.  Ablation targeted augmentation chỉ nếu đã định nghĩa rõ và còn ngân
    sách.

7.  Threshold board-level chọn validation.

8.  External dataset nếu có chỉ dùng để đánh giá domain shift, không
    trộn tùy tiện vào train.

## 4.5. Chỉ số đánh giá nên chốt

mAP@0.5:0.95, per-class Recall/F1, Recall theo size bins,
critical-defect FN rate, board-level false accept/false reject,
full-image latency, patch count, parameters/GFLOPs.

## 4.6. Phạm vi và giới hạn nên ghi rõ

PCB surface defect detection 6 classes; không tuyên bố cho sản phẩm công
nghiệp nói chung; không tuyên bố kích thước micromet nếu thiếu
calibration.

# 5. Đánh giá theo tiêu chí học thuật

| **Tiêu chí**         | **Đánh giá** | **Nhận xét ngắn**                                         |
|----------------------|--------------|-----------------------------------------------------------|
| Tính học thuật       | Tốt          | Bài toán small defect rõ và có error-cost framing.        |
| Tính mới             | Khá          | Giá trị ở tích hợp high-resolution detection và protocol. |
| Tính khả thi         | Khá          | Cần giảm số module.                                       |
| Thiết kế thực nghiệm | Tốt          | Ablation tốt nhưng đang quá rộng.                         |
| Tính tái lập         | Khá          | Group-aware split cần cụ thể hóa.                         |
| Mức cần chỉnh        | Cao          | Tên, dataset merge và scope improvements cần sửa.         |
