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
**Project & Work Manager** là hệ thống quản lý dự án và công việc chuyên sâu được xây dựng trên nền tảng Odoo 15. Hệ thống tập trung vào việc số hóa quy trình quản trị dự án phần mềm, tối ưu hóa sự phối hợp giữa các thành viên và khai phá tiềm năng tự động hóa thông qua trí tuệ nhân tạo (Generative AI).

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

### 2.1. Cài đặt công cụ, môi trường và các thư viện cần thiết

#### 2.1.1. Tải project.
```
git clone https://github.com/hiepnguyen05/Odoo-QuanLyDuAn-QuanLyCongViec.git
cd Odoo-QuanLyDuAn-QuanLyCongViec
```
#### 2.1.2. Cài đặt các thư viện cần thiết
Người sử dụng thực thi các lệnh sau đề cài đặt các thư viện cần thiết

```
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-distutils python3.10-dev build-essential libssl-dev libffi-dev zlib1g-dev python3.10-venv libpq-dev
```
#### 2.1.3. Khởi tạo môi trường ảo.
- Khởi tạo môi trường ảo
```
python3.10 -m venv ./venv
```
- Thay đổi trình thông dịch sang môi trường ảo
```
source venv/bin/activate
```
- Chạy requirements.txt để cài đặt tiếp các thư viện được yêu cầu
```
pip3 install -r requirements.txt
```
### 2.2. Setup database

Khởi tạo database trên docker bằng việc thực thi file dockercompose.yml.
```
sudo docker-compose up -d
```
### 2.3. Setup tham số chạy cho hệ thống
Tạo tệp **odoo.conf** có nội dung như sau:
```
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5431
xmlrpc_port = 8069
```
Có thể kế thừa từ file **odoo.conf.template**
### 2.4. Chạy hệ thống và cài đặt các ứng dụng cần thiết
Lệnh chạy
```
python3 odoo-bin.py -c odoo.conf -u all
```
Người sử dụng truy cập theo đường dẫn _http://localhost:8069/_ để đăng nhập vào hệ thống.


## 🤝 Đóng góp & Phát triển
Dự án được phát triển bởi **Nhóm 9 - Lớp CNTT 17-07** - Khoa CNTT - Đại học Đại Nam.
Trưởng nhóm & Chịu trách nhiệm Repo: **Nguyễn Ngọc Hiệp** (@hiepnguyen05).
