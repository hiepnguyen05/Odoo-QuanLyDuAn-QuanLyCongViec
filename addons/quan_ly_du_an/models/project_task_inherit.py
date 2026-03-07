# -*- coding: utf-8 -*-
"""
Kế thừa và mở rộng project.task
Thêm validation phân quyền gán công việc
"""

from datetime import timedelta
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
    
    task_status_class = fields.Char(compute='_compute_task_status', store=False)
    task_status_label = fields.Char(compute='_compute_task_status', store=False)

    # Ghi đè field date_deadline để thêm giá trị mặc định (7 ngày tới)
    date_deadline = fields.Date(
        default=lambda self: fields.Date.context_today(self) + timedelta(days=7)
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

    @api.depends('stage_id', 'date_deadline')
    def _compute_task_status(self):
        """Tính toán nhãn và màu sắc cho thẻ Kanban"""
        today = fields.Date.context_today(self)
        for task in self:
            # 1. Nếu Đã hoàn thành (Xanh)
            if task.stage_id and (task.stage_id.fold or getattr(task.stage_id, 'is_closed', False) or any(k in task.stage_id.name.lower() for k in ['xong', 'giao', 'hoàn thành', 'done'])):
                task.task_status_class = 'bg-success'
                task.task_status_label = 'Đã hoàn thành'
            # 2. Nếu Quá hạn (Đỏ) - Chưa hoàn thành mà hạn < hôm nay
            elif task.date_deadline and task.date_deadline < today:
                task.task_status_class = 'bg-danger'
                task.task_status_label = 'Quá hạn'
            # 3. Nếu Hôm nay (Vàng) - Chưa hoàn thành mà hạn == hôm nay
            elif task.date_deadline and task.date_deadline == today:
                task.task_status_class = 'bg-warning text-dark'
                task.task_status_label = 'Hôm nay'
            else:
                task.task_status_class = ''
                task.task_status_label = ''

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

    # ==================== ACTION TỪ VIEW TASK ====================
    def action_generate_tasks_ai_from_task(self):
        """
        Hàm được gọi từ nút nằm trên màn hình Tree/Kanban của Công Việc.
        Mục đích: Lấy ra được ID Dự án hiện tại để gọi sang hàm Sinh Task AI bên project
        """
        project_id = self.env.context.get('default_project_id') or self.env.context.get('active_id')
        
        if not project_id:
            raise ValidationError("❌ Không thể kết nối tới AI: Không tìm thấy Dự án gốc! Vô lại đúng Màn hình dự án nhé.")
            
        project = self.env['project.project'].browse(project_id)
        if not project.exists():
            raise ValidationError("❌ Dự án không tồn tại.")
        
        # Chuyền lệnh sang Project xử lý
        return project.action_generate_tasks_ai()
