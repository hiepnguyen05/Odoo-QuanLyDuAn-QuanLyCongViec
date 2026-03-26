# -*- coding: utf-8 -*-
{
    'name': "Quản lý Công việc",

    'summary': """
        Hệ thống quản lý công việc và nhiệm vụ (Đề tài 3)
    """,

    'description': """
        ĐỀ TÀI 3: PHẦN QUẢN LÝ CÔNG VIỆC
        =============================================
        - Kế thừa project.task
        - Quản lý Checklist công việc
        - Tự động hóa xếp loại KPI (A, B, C, D)
        - AI tạo SOP (Quy trình chuẩn) và Checklist
        - Gửi email thông báo và nhắc việc tự động
    """,

    'author': "Nhóm 9 - FIT DNU",
    'website': "https://github.com/FIT-DNU/Business-Internship",
    'category': 'Project Management',
    'version': '15.0.1.0.0',

    'depends': [
        'project',
        'hr',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/project_task_type_data.xml',
        'data/mail_data.xml',
        'views/project_task_views.xml',
        'views/menu.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
