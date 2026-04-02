<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
    PLATFORM ERP - PROJECT & WORK MANAGEMENT
</h2>
<div align="center">
    <p align="center">
        <img src="https://github.com/HOANGTHI2509/ORM_CNTT-1707/raw/main/docs/logo/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="https://github.com/HOANGTHI2509/ORM_CNTT-1707/raw/main/docs/logo/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="https://github.com/HOANGTHI2509/ORM_CNTT-1707/raw/main/docs/logo/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)
![Odoo](https://img.shields.io/badge/Odoo-16.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white)

</div>

> **Học Phần:** Hội nhập và quản trị phần mềm doanh nghiệp - Đề Tài 1
> **Đề tài:** Quản lý Dự án và Công việc
> **Nhóm thực hiện:** Nhóm 9 (Lớp CNTT 17-07)

## 📖 1. Giới thiệu
**Project & Work Manager** là hệ thống quản lý dự án và công việc chuyên sâu được xây dựng trên nền tảng Odoo 16. Hệ thống tập trung vào việc số hóa quy trình quản trị dự án phần mềm, tối ưu hóa sự phối hợp giữa các thành viên và khai phá tiềm năng tự động hóa thông qua trí tuệ nhân tạo (Generative AI).

### ✨ Những điểm nổi bật (Nhóm 9 - CNTT 17-07)
Dự án được thiết kế để giải quyết bài toán quản trị dự án quy mô vừa và lớn với các tính năng đột phá:

**1. Hệ sinh thái AI đột phá (Gemini AI Integration):**
- **AI Task Generator:** Tự động sinh hàng loạt công việc từ mô tả dự án, giúp tiết kiệm 80% thời gian lên kế hoạch.
- **AI SOP & Checklist:** Tự động xây dựng quy trình thực hiện chuẩn và danh sách kiểm tra chi tiết cho từng task.
- **AI Task Summary:** Tóm tắt thông minh nội dung công việc, hỗ trợ quản lý review nhanh tiến độ.

**2. Quản trị Kanban & Tiến độ thông minh:**
- **Compact Kanban UI:** Giao diện thẻ công việc tinh gọn, hiển thị đầy đủ thông tin quan trọng.
- **5 Trạng thái Chuẩn:** Mới, Đang thực hiện, Tạm dừng, Đã hoàn thành, Đã hủy.
- **Real-time Tracking:** Tiến độ % được tính toán tự động dựa trên mức độ hoàn thiện của Checklist.

**3. Tự động hóa & KPI:**
- **KPI Rating:** Tự động xếp loại hiệu quả công việc (A/B/C/D) dựa trên thời gian hoàn thành thực tế và Deadline.
- **Email Notification:** Tự động gửi email giao việc, nhắc deadline và thông báo hoàn thành dự án.

### Các module chính:
1.  **Quản lý Dự án (`quan_ly_du_an`)**: Quản trị danh mục dự án, thiết lập đội ngũ và giai đoạn.
2.  **Quản lý Công việc (`quan_ly_cong_viec`)**: Phân hệ trọng tâm tích hợp AI, checklist và theo dõi KPI.
3.  **Quản lý Nhân sự (`nhan_su`)**: Quản lý hồ sơ nhân viên và lịch sử công tác gắn liền với các dự án.

## 🚀 2. Hướng dẫn Cài đặt & Sử dụng

### 2.1. Clone dự án
```bash
git clone https://github.com/hiepnguyen05/Odoo-QuanLyDuAn-QuanLyCongViec.git
cd Odoo-QuanLyDuAn-QuanLyCongViec
```

### 2.2. Cài đặt môi trường (Ubuntu/WSL)
Yêu cầu: `Python 3.10`, `PostgreSQL 14+`.

```bash
# Cài đặt thư viện hệ thống
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-dev build-essential libpq-dev

# Tạo môi trường ảo & cài dependencies
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3. Cấu hình Odoo & Gemini AI
1. Tạo file `odoo.conf` với `addons_path = addons`.
2. Khởi động Odoo và cài đặt các module: `nhan_su`, `quan_ly_du_an`, `quan_ly_cong_viec`.
3. Cấu hình Gemini API: Vào **Thiết lập -> Kỹ thuật -> Thông số hệ thống**, thêm key `gemini.api_key`.

### 2.4. Chạy hệ thống
```bash
python3 odoo-bin -c odoo.conf -u nhan_su,quan_ly_du_an,quan_ly_cong_viec
```
Truy cập: `http://localhost:8069`

## 🤝 Đóng góp & Phát triển
Dự án được phát triển bởi **Nhóm 9 - Lớp CNTT 17-07** - Khoa CNTT - Đại học Đại Nam.
Trưởng nhóm & Chịu trách nhiệm Repo: **Nguyễn Ngọc Hiệp** (@hiepnguyen05).
