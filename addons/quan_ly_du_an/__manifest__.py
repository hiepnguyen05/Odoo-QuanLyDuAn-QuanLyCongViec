# -*- coding: utf-8 -*-
{
    'name': "Quản lý Dự án & Công việc",

    'summary': """
        Hệ thống quản lý dự án tích hợp với HRM (Đề tài 3)
    """,

    'description': """
        ĐỀ TÀI 3: QUẢN LÝ DỰ ÁN + QUẢN LÝ CÔNG VIỆC
        =============================================
        
        MỨC 1 - TÍCH HỢP HỆ THỐNG:
        - Kế thừa hr.employee (HRM)
        - Quản lý thành viên dự án
        - Validation phân quyền gán công việc
        - Tính tiến độ dự án
        - Lọc "Công việc của tôi"
        
        MỨC 2 - TỰ ĐỘNG HÓA:
        - Tự động tạo task mẫu
        - Tự động chuyển trạng thái
        - Tự động gửi thông báo
        
        MỨC 3 - CÔNG NGHỆ MỚI:
        - AI tóm tắt dự án
        - Đồng bộ Google Calendar
        - Gửi thông báo Telegram
    """,

    'author': "Nhóm 9 - FIT DNU",
    'website': "https://github.com/FIT-DNU/Business-Internship",
    'category': 'Project Management',
    'version': '1.0.5',

    # Module phụ thuộc
    'depends': [
        'base',
        'hr',
        'project',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/project_task_type_data.xml',
        'views/hr_employee_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/menu.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
