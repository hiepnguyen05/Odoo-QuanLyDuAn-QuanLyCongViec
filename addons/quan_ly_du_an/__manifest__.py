# -*- coding: utf-8 -*-
{
    'name': "Quản lý Dự án",

    'summary': """
        Hệ thống quản lý dự án tích hợp với HRM (Đề tài 3)
    """,

    'description': """
        ĐỀ TÀI 3: PHẦN QUẢN LÝ DỰ ÁN
        =============================================
        
        MỨC 1 - TÍCH HỢP HỆ THỐNG:
        - Kế thừa hr.employee (HRM)
        - Quản lý thành viên dự án
        - Tính tiến độ dự án
        
        MỨC 2 - TỰ ĐỘNG HÓA:
        - Tự động tạo task mẫu (từ Loại dự án)
        - Tự động chuyển trạng thái dự án
        
        MỨC 3 - CÔNG NGHỆ MỚI:
        - AI tóm tắt/gợi ý dự án
        - Dashboard báo cáo chuyên sâu
    """,

    'author': "Nhóm 9 - FIT DNU",
    'website': "https://github.com/FIT-DNU/Business-Internship",
    'category': 'Project Management',
    'version': '15.0.1.0.1',

    # Module phụ thuộc
    'depends': [
        'base',
        'hr',
        'project',
        'quan_ly_cong_viec',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/project_project_views.xml',
        'views/project_type_views.xml',
        'views/project_dashboard_views.xml',
        'views/project_report_views.xml',
        'wizard/ai_task_generator_wizard_views.xml',
        'views/menu.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
