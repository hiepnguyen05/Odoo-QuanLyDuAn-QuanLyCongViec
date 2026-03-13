# -*- coding: utf-8 -*-
"""
Kế thừa và mở rộng hr.employee
Thêm thông tin CCCD, Quê quán và các validation
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class HrEmployeeExtend(models.Model):
    """Kế thừa hr.employee để thêm thông tin bổ sung"""
    _inherit = 'hr.employee'
    
    def __init__(self, pool, cr):
        """Log khi model được khởi tạo"""
        _logger.info("="*50)
        _logger.info("QUAN_LY_DU_AN: HrEmployeeExtend model is being initialized!")
        _logger.info("="*50)
        super(HrEmployeeExtend, self).__init__(pool, cr)
    
    # ==================== FIELDS ====================
    
    birthday = fields.Date(string='Ngày sinh', required=True)
    
    que_quan = fields.Char(
        string='Quê quán',
        required=True,
        help='Địa chỉ quê quán của nhân viên',
        tracking=True
    )
    
    so_cccd = fields.Char(
        string='Số CCCD',
        required=True,
        help='Số Căn cước công dân (12 số)',
        copy=False,
        tracking=True
    )
    
    ngay_cap = fields.Date(
        string='Ngày cấp CCCD',
        required=True,
        help='Ngày cấp Căn cước công dân',
        tracking=True
    )
    
    noi_cap = fields.Char(
        string='Nơi cấp CCCD',
        required=True,
        help='Nơi cấp Căn cước công dân',
        default='Cục Cảnh sát ĐKQL cư trú và DLQG về dân cư',
        tracking=True
    )
    
    tuoi = fields.Integer(
        string='Tuổi',
        compute='_compute_tuoi',
        store=False,
        help='Tuổi được tính từ ngày sinh'
    )
    
    family_ids = fields.One2many('hr.family', 'employee_id', string="Danh sách thân nhân")
    work_history_ids = fields.One2many('hr.work.history', 'employee_id', string="Quá trình công tác")
    
    # ==================== COMPUTED METHODS ====================
    
    @api.depends('birthday')
    def _compute_tuoi(self):
        """Tính tuổi từ ngày sinh"""
        today = date.today()
        for record in self:
            if record.birthday:
                age = today.year - record.birthday.year
                if today.month < record.birthday.month or \
                   (today.month == record.birthday.month and today.day < record.birthday.day):
                    age -= 1
                record.tuoi = age
            else:
                record.tuoi = 0
                
    # ==================== CONSTRAINTS ====================
    
    @api.constrains('birthday')
    def _check_birthday(self):
        """Kiểm tra ngày sinh không được lớn hơn ngày hiện tại"""
        for record in self:
            if record.birthday and record.birthday > fields.Date.today():
                raise ValidationError(
                    "❌ Ngày sinh không hợp lệ!\n\n"
                    f"Ngày sinh đã nhập: {record.birthday}\n"
                    f"Ngày hiện tại: {fields.Date.today()}\n\n"
                    "💡 Ngày sinh không được lớn hơn ngày hiện tại."
                )
    
    @api.constrains('so_cccd')
    def _check_so_cccd(self):
        """Kiểm tra số CCCD: định dạng và không trùng lặp"""
        for record in self:
            if record.so_cccd:
                # Kiểm tra định dạng
                if not record.so_cccd.isdigit() or len(record.so_cccd) != 12:
                    raise ValidationError(
                        "❌ Số CCCD không hợp lệ!\n\n"
                        f"Số CCCD đã nhập: {record.so_cccd} ({len(record.so_cccd)} ký tự)\n\n"
                        "💡 Số CCCD phải là 12 chữ số."
                    )
                
                # Kiểm tra trùng lặp
                duplicate = self.search([
                    ('so_cccd', '=', record.so_cccd),
                    ('id', '!=', record.id)
                ], limit=1)
                
                if duplicate:
                    raise ValidationError(
                        f"❌ Số CCCD '{record.so_cccd}' đã tồn tại!\n\n"
                        f"Nhân viên: {duplicate.name}\n"
                        f"Mã NV: {duplicate.employee_id or 'Chưa có'}\n\n"
                        "💡 Mỗi nhân viên phải có số CCCD riêng biệt."
                    )
    
    @api.constrains('ngay_cap', 'birthday')
    def _check_ngay_cap(self):
        """Kiểm tra ngày cấp CCCD hợp lệ"""
        for record in self:
            if record.ngay_cap:
                if record.ngay_cap > fields.Date.today():
                    raise ValidationError(
                        "❌ Ngày cấp CCCD không hợp lệ!\n\n"
                        f"Ngày cấp đã nhập: {record.ngay_cap}\n"
                        f"Ngày hiện tại: {fields.Date.today()}\n\n"
                        "💡 Ngày cấp không được lớn hơn ngày hiện tại."
                    )
                
                if record.birthday:
                    age_at_issue = (record.ngay_cap - record.birthday).days / 365.25
                    if age_at_issue < 14:
                        raise ValidationError(
                            "❌ Ngày cấp CCCD không hợp lệ!\n\n"
                            f"Tuổi khi cấp: {age_at_issue:.1f} năm\n\n"
                            "💡 Công dân phải đủ 14 tuổi mới được cấp CCCD."
                        )
    
    # ==================== KPI PERFORMANCE FIELDS (Mức 2) ====================
    
    kpi_average = fields.Float(
        string='Điểm KPI Trung bình',
        compute='_compute_kpi_performance',
        store=False,
        group_operator="avg"
    )
    
    task_done_count = fields.Integer(
        string='Số việc đã xong',
        compute='_compute_kpi_performance',
        store=False
    )
    
    task_late_count = fields.Integer(
        string='Số việc trễ hạn',
        compute='_compute_kpi_performance',
        store=False
    )

    def _compute_kpi_performance(self):
        """Tính toán thống kê hiệu suất công việc từ các task được gán"""
        kpi_map = {'a': 100.0, 'b': 80.0, 'c': 60.0, 'd': 40.0}
        
        for employee in self:
            # Tìm các task mà nhân viên này tham gia (qua field nhan_vien_ids)
            tasks = self.env['project.task'].search([
                ('nhan_vien_ids', 'in', [employee.id]),
                ('date_completed', '!=', False) # Chỉ tính các việc đã xong
            ])
            
            employee.task_done_count = len(tasks)
            employee.task_late_count = len(tasks.filtered(lambda t: t.kpi_rating in ['c', 'd']))
            
            if tasks:
                total_score = sum(kpi_map.get(t.kpi_rating, 0.0) for t in tasks)
                employee.kpi_average = total_score / len(tasks)
            else:
                employee.kpi_average = 0.0

    def action_view_employee_tasks(self):
        """Smart button mở danh sách công việc của nhân viên này"""
        self.ensure_one()
        return {
            'name': 'Công việc được gán',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'kanban,tree,form',
            'domain': [('nhan_vien_ids', 'in', [self.id])],
            'context': {'default_nhan_vien_ids': [(4, self.id)]},
        }

    # ==================== OVERRIDE METHODS ====================
    # (Đã loại bỏ name_get do hr.employee mặc định không có trường employee_id)
