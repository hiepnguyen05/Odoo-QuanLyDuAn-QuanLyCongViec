# -*- coding: utf-8 -*-
"""
Kế thừa và mở rộng project.task
Thêm validation phân quyền gán công việc
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """Kế thừa project.task để thêm validation phân quyền"""
    _inherit = 'project.task'
    
    # ==================== FIELDS ====================
    nhan_vien_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='project_task_employee_rel',
        column1='task_id',
        column2='employee_id',
        string='Nhân viên thực hiện',
        help='Danh sách nhân viên được giao việc (không cần User)'
    )

    # Ghi đè field date_deadline để thêm giá trị mặc định (7 ngày tới)
    date_deadline = fields.Date(
        default=lambda self: fields.Date.to_string(fields.Date.context_today(self) + fields.Date.timedelta(days=7))
    )

    # ==================== CONSTRAINTS ====================
    
    @api.constrains('date_deadline')
    def _check_date_deadline(self):
        """Chặn chọn hạn chót trong quá khứ"""
        for task in self:
            if task.date_deadline and task.date_deadline < fields.Date.today():
                raise ValidationError(
                    "❌ Hạn chót không hợp lệ!\n\n"
                    "Lý do: Hạn chót không được nằm trong quá khứ.\n"
                    "💡 Vui lòng chọn ngày hôm nay hoặc một ngày trong tương lai."
                )

    @api.constrains('nhan_vien_ids', 'project_id')
    def _check_employee_in_project_team(self):
        """
        Kiểm tra người được gán task phải nằm trong danh sách thành viên dự án
        """
        for task in self:
            if task.project_id and task.nhan_vien_ids:
                project_employees = task.project_id.thanh_vien_ids
                
                if not project_employees:
                    continue
                
                for employee in task.nhan_vien_ids:
                    if employee not in project_employees:
                        raise ValidationError(
                            f"❌ Không thể gán công việc!\n\n"
                            f"Nhân viên: {employee.name}\n"
                            f"Lý do: Nhân viên này không thuộc dự án '{task.project_id.name}'\n\n"
                            f"💡 Giải pháp:\n"
                            f"1. Thêm nhân viên vào danh sách thành viên dự án, HOẶC\n"
                            f"2. Chọn nhân viên khác đã có trong dự án"
                        )

    # ==================== ONCHANGE METHODS ====================
    
    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Khi chọn dự án:
        - Giới hạn danh sách nhân viên chỉ hiển thị thành viên của dự án đó
        - Xóa nhân viên đã chọn nếu không thuộc dự án mới
        """
        if self.project_id and self.project_id.thanh_vien_ids:
            valid_employee_ids = self.project_id.thanh_vien_ids.ids
            
            if self.nhan_vien_ids:
                invalid_employees = self.nhan_vien_ids.filtered(lambda e: e.id not in valid_employee_ids)
                if invalid_employees:
                    self.nhan_vien_ids = [(3, employee.id) for employee in invalid_employees]
            
            return {
                'domain': {
                    'nhan_vien_ids': [('id', 'in', valid_employee_ids)]
                }
            }
        else:
            return {
                'domain': {
                    'nhan_vien_ids': []
                }
            }
