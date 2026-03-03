# -*- coding: utf-8 -*-
"""
Kế thừa và mở rộng project.project
Thêm quản lý thành viên dự án và tính tiến độ
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    """Kế thừa project.project để thêm quản lý thành viên"""
    _inherit = 'project.project'
    
    # ==================== FIELDS ====================
    
    thanh_vien_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='project_employee_rel',
        column1='project_id',
        column2='employee_id',
        string='Thành viên dự án',
        help='Danh sách nhân viên được phép tham gia dự án này'
    )
    
    so_luong_thanh_vien = fields.Integer(
        string='Số lượng thành viên',
        compute='_compute_so_luong_thanh_vien',
        store=True,
        help='Tổng số thành viên trong dự án'
    )
    
    progress = fields.Float(
        string='Tiến độ (%)',
        compute='_compute_progress',
        store=True,
        help='Tiến độ được tính tự động từ % hoàn thành của các task'
    )
    
    # ==================== COMPUTED METHODS ====================
    
    @api.depends('thanh_vien_ids')
    def _compute_so_luong_thanh_vien(self):
        """Tính số lượng thành viên trong dự án"""
        for record in self:
            record.so_luong_thanh_vien = len(record.thanh_vien_ids)
    
    @api.depends('task_ids', 'task_ids.stage_id', 'task_ids.stage_id.fold')
    def _compute_progress(self):
        """
        Tính % tiến độ dự án dựa trên số task hoàn thành
        Công thức: (Số task Done / Tổng số task) * 100
        """
        for project in self:
            tasks = project.task_ids
            if tasks:
                completed_tasks = tasks.filtered(lambda t: t.stage_id.fold)
                project.progress = (len(completed_tasks) / len(tasks)) * 100
            else:
                project.progress = 0.0
    
    # ==================== ACTION METHODS ====================
    
    def action_view_tasks(self):
        """Smart button để xem danh sách task của dự án"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Công việc',
            'res_model': 'project.task',
            'view_mode': 'tree,form,kanban',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_project_id': self.id,
            },
            'target': 'current',
        }
    
    def action_view_team_members(self):
        """Smart button để xem danh sách thành viên dự án"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Thành viên dự án',
            'res_model': 'hr.employee',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', self.thanh_vien_ids.ids)],
            'target': 'current',
        }
    
    # ==================== CONSTRAINTS ====================
    
    @api.constrains('thanh_vien_ids')
    def _check_thanh_vien_ids(self):
        """Kiểm tra phải có ít nhất 1 thành viên trong dự án"""
        for record in self:
            if record.thanh_vien_ids and len(record.thanh_vien_ids) == 0:
                raise ValidationError(
                    "❌ Dự án phải có ít nhất 1 thành viên!"
                )
