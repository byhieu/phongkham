# HỆ THỐNG QUẢN LÝ PHÒNG KHÁM BỆNH TƯ NHÂN
> **Bài tập lớn môn Cơ sở dữ liệu – Project 1 (MySQL 8 + Python Streamlit)**

Ứng dụng web trực quan, thân thiện cho người không biết lập trình, kết nối trực tiếp với MySQL 8 để thực thi các nghiệp vụ phòng khám qua các Stored Procedure, Trigger và View.

---

## 📁 Cấu trúc thư mục

```text
btl_csdl/
├── phong_kham.sql      # Script tạo CSDL MySQL 8, trigger, procedure, dữ liệu mẫu
├── app.py              # Giao diện ứng dụng Streamlit (Đầy đủ 13 phân hệ chức năng)
├── db.py               # Module kết nối MySQL, gọi Stored Procedure, xử lý lỗi hệ thống
├── requirements.txt    # Danh sách thư viện Python cần cài đặt
├── .env.example        # File mẫu cấu hình kết nối CSDL
├── .env                # File cấu hình kết nối thực tế (không commit lên Git)
├── .gitignore          # Cấu hình bỏ qua file nhạy cảm (.env, cache)
└── README.md           # Hướng dẫn cài đặt và sử dụng chi tiết
```

---

## 🛠️ Yêu cầu hệ thống

* **Hệ điều hành:** Windows, macOS hoặc Linux.
* **Hệ quản trị CSDL:** **MySQL 8.0.16+** (yêu cầu hỗ trợ CHECK constraint, Trigger và Window Functions).
* **Python:** Phiên bản **3.10 trở lên** (đã kiểm thử tốt trên Python 3.13).

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy (Từng bước)

### Bước 1: Nạp cơ sở dữ liệu `phong_kham.sql` vào MySQL

Mở **MySQL Workbench** hoặc mở **Command Prompt / Terminal** và thực hiện:

* **Cách 1: Sử dụng MySQL Workbench**
  1. Mở MySQL Workbench, kết nối vào tài khoản `root`.
  2. Chọn menu `File` $\rightarrow$ `Open SQL Script...` $\rightarrow$ chọn file `phong_kham.sql`.
  3. Bấm nút biểu tượng tia sét ⚡ (**Execute All**) để chạy toàn bộ file.

* **Cách 2: Sử dụng dòng lệnh Terminal**
  ```bash
  mysql -u root -p < phong_kham.sql
  ```
  *(Nhập mật khẩu MySQL khi được hỏi)*.

---

### Bước 2: Cài đặt các thư viện Python

Mở terminal trong thư mục dự án (`c:\Dev\btl_csdl`) và chạy lệnh:

```bash
pip install -r requirements.txt
```

---

### Bước 3: Cấu hình file `.env`

1. Tạo file `.env` dựa trên file mẫu `.env.example`:
   * Nếu dùng lệnh terminal:
     ```bash
     copy .env.example .env
     ```
2. Mở file `.env` và điền thông tin tài khoản MySQL của bạn:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=mat_khau_mysql_cua_ban
   DB_NAME=phong_kham
   ```
   *(Nếu tài khoản `root` không đặt mật khẩu, để trống `DB_PASSWORD=`)*.

> 💡 **Mẹo:** Bạn cũng có thể sửa mật khẩu và cấu hình kết nối trực tiếp ngay trên giao diện web ở thanh bên trái (Sidebar) mà không cần mở file text.

---

### Bước 4: Khởi chạy ứng dụng Web

Chạy lệnh sau trong thư mục dự án:

```bash
python -m streamlit run app.py
```
*(hoặc `streamlit run app.py` nếu thư mục Scripts đã có trong PATH)*.

Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ: **http://localhost:8501** 🎉

---

## 📖 Hướng dẫn sử dụng các chức năng trên giao diện

Hệ thống cung cấp **13 phân hệ chức năng** tại thanh điều hướng bên trái (Sidebar):

### A. Nhóm Tra cứu & Báo cáo:
1. **📋 1. Bệnh theo tháng:** Tra cứu số bệnh nhân mắc theo từng tháng, sắp xếp giảm dần kèm biểu đồ cột trực quan. Một bệnh nhân khám nhiều lần liên tiếp cho cùng một bệnh chỉ tính là một lần mắc.
2. **💰 2. Bảng lương Bác sỹ & Y tá:** Tính lương theo quy tắc: Bác sỹ (7tr + 1tr/đợt chữa khỏi), Y tá (5tr + 200k/lần khám hỗ trợ). Hỗ trợ xem tháng hiện tại (Tháng 11/2026) hoặc chọn tháng cụ thể.
3. **🔍 3. Tra cứu hồ sơ bệnh nhân:** Dropdown chọn bệnh nhân, xem Thông tin cá nhân, Tình trạng bệnh hiện tại (đang điều trị), và Toàn bộ lịch sử khám chữa bệnh.
4. **📈 4. Báo cáo doanh thu:** Doanh thu tiền khám và tiền thuốc theo khoảng ngày và theo từng tháng.

### B. Nhóm Quản lý Dữ liệu Nghiệp vụ:
5. **👥 5. Quản lý bệnh nhân:** Tìm kiếm bệnh nhân theo tên, mã số, số CMT/CCCD. Thêm mới, chỉnh sửa và xóa hồ sơ bệnh nhân.
6. **🏥 6. Mở đợt bệnh mới:** Tiếp nhận bệnh nhân, chọn bệnh mắc phải, bác sỹ phụ trách và ngày bắt đầu. Mỗi bệnh nhân chỉ có một đợt đang điều trị cho cùng một bệnh.
7. **🩺 7. Thêm lần khám:** Ghi nhận lần khám của bệnh nhân trong đợt điều trị. Ngày vào khám phải nằm trong khoảng thời gian điều trị của đợt bệnh.
8. **💊 8. Kê đơn thuốc cho lần khám:** Chọn lần khám, chọn thuốc từ danh mục và nhập số lượng. Đơn giá thuốc và tổng tiền viện phí tự động được cập nhật.
9. **👩‍⚕️ 9. Phân công y tá hỗ trợ:** Chọn lần khám, chọn y tá và vai trò hỗ trợ (*Tiếp đón*, *Cấp thuốc*, *Tiêm thuốc*, *Chăm sóc theo dõi*). Mỗi lần khám có tối đa 3 y tá tham gia hỗ trợ.
10. **🎉 10. Ghi nhận chữa khỏi (Đóng đợt):** Ghi nhận ngày kết thúc và chữa khỏi bệnh cho bệnh nhân. Ngày kết thúc không được sớm hơn ngày vào của lần khám cuối cùng.
11. **💊 11. Quản lý thuốc và bệnh:** Xem danh mục, thêm thuốc mới, cập nhật giá thuốc; xem và thêm loại bệnh mới vào hệ thống.
12. **👨‍⚕️ 12. Thêm bác sỹ, y tá:** Thêm Bác sỹ mới (bậc nghề, trình độ đào tạo, chuyên môn) và Y tá mới (trình độ đào tạo).

### C. Kiểm tra Ràng buộc:
13. **🛡️ 13. Kiểm tra ràng buộc dữ liệu:** Chạy tự động 8 bài kiểm thử nghiệp vụ hoặc thử nghiệm trực tiếp từng tình huống vi phạm quy tắc để kiểm chứng thông báo lỗi tiếng Việt từ hệ thống. Chi tiết kỹ thuật được xếp gọn trong mục có thể mở rộng.

---

## ❓ Xử lý sự cố thường gặp (Troubleshooting)

1. **Lỗi `Access denied for user 'root'@'localhost'`:**
   * Mật khẩu trong file `.env` chưa khớp với mật khẩu MySQL của bạn.
   * Cách khắc phục: Nhập mật khẩu đúng vào ô **DB Password** tại thanh bên trái và bấm **Lưu .env**.
2. **Lỗi `Can't connect to MySQL server on 'localhost'`:**
   * Dịch vụ MySQL chưa được khởi động. Hãy mở `services.msc` trên Windows và đảm bảo dịch vụ `MySQL80` đang ở trạng thái `Running`.
3. **Lỗi `Unknown database 'phong_kham'`:**
   * Bạn chưa nạp file `phong_kham.sql` vào MySQL. Hãy thực hiện Bước 1 ở trên.
