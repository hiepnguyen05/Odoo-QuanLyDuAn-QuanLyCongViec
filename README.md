# Hệ thống Quản trị Dự án & Nhân sự Tích hợp AI (Nhóm 9)

![Odoo](https://img.shields.io/badge/Odoo-16.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

Dự án phát triển module mở rộng cho Odoo 16 nhằm tối ưu hóa việc quản lý dự án và nhân sự trong các doanh nghiệp phần mềm, tích hợp tự động hóa kịch bản và trí tuệ nhân tạo (Gemini AI).

---

## 🌟 Tính năng nổi bật

### 🟢 Mức 1: Quản trị cốt lõi
* **Tích hợp HRM & Project**: Quản lý thành viên dự án chặt chẽ, mở rộng thông tin nhân sự (gia đình, lịch sử công tác).
* **Ràng buộc an toàn**: Chỉ cho phép gán công việc cho nhân viên thuộc dự án.
* **Tiến độ Real-time**: Tự động tính % hoàn thành dự án ngay trên giao diện Kanban.

### 🔵 Mức 2: Tự động hóa (Automation)
* **Kịch bản mẫu**: Tự động sinh hàng loạt công việc mẫu khi chọn loại dự án (Mobile, Web, Backend...).
* **KPI thông minh**: Tự động xếp loại KPI (A, B, C, D) dựa trên Deadline và thời gian thực tế.
* **Hệ thống nhắc việc**: Tự động gửi Email thông báo giao việc và nhắc nhở hạn chót hàng ngày.

### 🟣 Mức 3: Đột phá AI & Analytics
* **Advanced AI Task Generator**: Gemini AI tự động sinh danh sách công việc, viết sẵn **Quy trình chuẩn (SOP)** và **Danh sách kiểm tra (Checklist)**.
* **BI Dashboard**: Hệ thống biểu đồ KPI và Pivot chuyên sâu giúp theo dõi hiệu suất toàn đội ngũ.

---

## 🚀 Hướng dẫn cài đặt

### 1. Cài đặt môi trường
```bash
# Clone dự án
git clone https://github.com/hiepnguyen05/Odoo-QuanLyDuAn-QuanLyCongViec.git
cd Odoo-QuanLyDuAn-QuanLyCongViec

# Khởi tạo môi trường ảo
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Cấu hình hệ thống
1. Tạo tệp `odoo.conf` (tham khảo `odoo.conf.template`).
2. Khởi động Odoo và cài đặt module `quan_ly_du_an`.
3. Cấu hình Gemini API: Vào **Thiết lập -> Kỹ thuật -> Thông số hệ thống**, thêm key `gemini.api_key`.
4. Cấu hình Email: Thiết lập **Outgoing Mail Server** để kích hoạt tính năng thông báo.

### 3. Lệnh chạy
```bash
python3 odoo-bin -c odoo.conf -u quan_ly_du_an
```

---
*Phát triển bởi Nhóm 9 - CNTT15_03.*

