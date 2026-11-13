NOTES.md: Bàn giao ngữ cảnh dự án (BTL CSDL, Phòng khám An Tâm)

AI mới đọc file này trước khi làm bất cứ việc gì.

1. Dự án
App quản lý phòng khám: Python + Streamlit + MySQL 8 (DB phong_kham).
File chính: app.py (UI), db.py (kết nối, gọi sp_*, bắt lỗi SIGNAL), phong_kham.sql (schema, trigger, procedure, dữ liệu mẫu, test), requirements.txt, README.md, .env / .env.example, .gitignore, .streamlit/config.toml.
Chạy: python -m streamlit run app.py (http://localhost:8501).
Thời điểm dữ liệu mẫu: tháng 11/2026.
2. QUY TẮC CỨNG
KHÔNG sửa phong_kham.sql.
Không viết lại logic ràng buộc ở tầng app: để trigger MySQL tự kiểm tra, app bắt lỗi (mã 1644 / SQLSTATE 45000) và hiển thị MESSAGE_TEXT bằng st.error. Ghi thành công thì st.success và làm mới dữ liệu.
Mọi nghiệp vụ tra cứu gọi qua procedure sp_*.
Giao diện cho người không biết code: KHÔNG hiện chữ trg_, sp_, SQLSTATE, SIGNAL, DENSE_RANK ra màn hình. Chữ mô tả dùng màu bình thường, không xám nhạt.
Validate đầu vào: CMT/CCCD đúng 12 chữ số, SĐT 10-11 chữ số (có thể để trống). Báo lỗi tiếng Việt.
Không có nút st.button thừa (đã xoá btn_tim, btn_calc, btn_view, btn_dt, btn_refresh). Giữ nguyên các st.form_submit_button. Kết quả tự cập nhật theo ô chọn. Mục doanh thu mặc định từ đầu tháng đến datetime.date.today().
3. Đã xong
Bước 1 (SQL): sửa lan_mac_thu dùng DENSE_RANK, thêm trigger BEFORE UPDATE, dữ liệu mẫu 11/2026, bộ test sp_chay_tat_ca_test (8 test).
Bước 2: app 13 mục sidebar (5 tra cứu và 8 quản lý dữ liệu), đã làm sạch thuật ngữ, validate, theme teal (primary 
#087e78, nền 
#f4f8f7, chữ 
#183b42, viền 
#d5e5e4, bo 15px, focus 
#e39d48), header "✚ Phòng khám An Tâm / Quản lý cơ sở dữ liệu", dòng mô tả dưới mỗi st.header (màu 
#5c7377), footer "Dữ liệu minh hoạ • MySQL 8 • Streamlit", không dùng logo tải từ internet.
4. ĐANG LÀM DỞ: Đổi sang menu NGANG 5 mục

Hết quota giữa chừng khi subagent đang viết lại app.py. Kiểm tra app.py có bị ghi dở không; nếu hỏng thì khôi phục từ app.py.bak hoặc app.py.v2.bak (hoặc git checkout app.py), rồi làm lại.

Yêu cầu:

Dùng st.radio(horizontal=True, label_visibility="collapsed") + CSS thành menu pill (hover nền 
#e6f5f2, mục đang chọn đậm). Ẩn sidebar.
"Cấu hình kết nối MySQL" chuyển thành st.expander ở cuối trang.
Giữ nguyên toàn bộ logic và hàm hiện có, chỉ sắp xếp lại chỗ đặt (số mục dưới đây là số trong bản 13 mục cũ).

Ánh xạ 5 mục:

Tổng quan (MỚI): 4 thẻ số liệu (bệnh nhân, bác sỹ, y tá, đợt đang điều trị); bảng 8 lần khám gần đây; mỗi bác sỹ x/30 đợt đang điều trị.
Bệnh nhân: tab "Tra cứu hồ sơ" (mục 3 cũ) và tab "Quản lý bệnh nhân" (mục 5 cũ).
Danh sách: bảng bác sỹ, y tá, bệnh nhân, thuốc, bệnh; mỗi dòng có Sửa và Xóa. Dùng lại quản lý thuốc/bệnh (mục 11 cũ) và thêm bác sỹ/y tá (mục 12 cũ).
Báo cáo: các tab "Bệnh theo tháng" (mục 1), "Lương" (mục 2, giữ khối "Cách tính lương theo đề bài"), "Doanh thu" (mục 4), "Kiểm tra ràng buộc" (mục 13, mô tả kỹ thuật nằm trong expander "Chi tiết kỹ thuật" mặc định đóng).
Nhập dữ liệu: các tab "Mở đợt bệnh" (6), "Thêm lần khám" (7), "Kê đơn thuốc" (8), "Phân công y tá" (9), "Ghi nhận chữa khỏi" (10).

Mỗi trang ở mục 6, 7, 9, 10 cũ chỉ có MỘT dòng st.caption tiếng Việt giải thích ràng buộc, ví dụ: "Mỗi bệnh nhân chỉ có một đợt đang điều trị cho cùng một bệnh."

Sau khi xong: chạy app, tự thử từng tab, báo kết quả.

5. Gợi ý cách làm để không hết quota giữa chừng
Viết app.py theo từng phần (mỗi tab/trang một hàm page_xxx()), hoặc tách module (pages/…), đừng viết một lần 1500 dòng.
Commit git sau mỗi phần chạy được.