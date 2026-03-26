# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    checklist_ids = fields.One2many(
        'project.task.checklist', 
        'task_id', 
        string='Danh sách kiểm tra (AI Suggest)'
    )
    
    ai_sop = fields.Html(
        string='Quy trình thực hiện (AI SOP)',
        help='Quy trình chi tiết do AI gợi ý cho công việc này'
    )
    
    nhan_vien_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='project_task_employee_rel',
        column1='task_id',
        column2='employee_id',
        string='Nhân viên thực hiện',
        help='Danh sách nhân viên được giao việc (không cần User)'
    )

    planned_date_begin = fields.Datetime(string='Ngày bắt đầu')
    
    completion_percentage = fields.Float(
        string='Tiến độ (%)', 
        compute='_compute_completion_percentage', 
        store=True
    )
    
    task_status_class = fields.Char(compute='_compute_task_status', store=False)
    task_status_label = fields.Char(compute='_compute_task_status', store=False)

    @api.depends('checklist_ids', 'checklist_ids.is_done')
    def _compute_completion_percentage(self):
        for task in self:
            if not task.checklist_ids:
                task.completion_percentage = 0.0
            else:
                done_count = len(task.checklist_ids.filtered(lambda c: c.is_done))
                total_count = len(task.checklist_ids)
                task.completion_percentage = (done_count / total_count) * 100

    date_completed = fields.Datetime(
        string='Ngày hoàn thành thực tế', 
        readonly=True, 
        copy=False
    )
    kpi_rating = fields.Selection([
        ('a', 'Xuất sắc (A)'),
        ('b', 'Tốt (B)'),
        ('c', 'Trung bình (C)'),
        ('d', 'Trễ hạn (D)')
    ], string='Xếp loại KPI', readonly=True, copy=False)

    date_deadline = fields.Date(
        default=lambda self: fields.Date.context_today(self) + timedelta(days=7)
    )

    @api.constrains('date_deadline')
    def _check_date_deadline(self):
        for task in self:
            if task.date_deadline and task.date_deadline < fields.Date.today():
                raise ValidationError(
                    "❌ Hạn chót không hợp lệ!\n\n"
                    "Lý do: Hạn chót không được nằm trong quá khứ."
                )

    @api.constrains('nhan_vien_ids', 'project_id')
    def _check_employee_in_project_team(self):
        for task in self:
            if task.project_id and task.nhan_vien_ids:
                if hasattr(task.project_id, 'thanh_vien_ids'):
                    project_employees = task.project_id.thanh_vien_ids
                    for employee in task.nhan_vien_ids:
                        if employee not in project_employees:
                            raise ValidationError(
                                f"❌ Không thể gán công việc!\n\n"
                                f"Nhân viên: {employee.name}\n"
                                f"Lý do: Nhân viên này không thuộc dự án '{task.project_id.name}'"
                            )

    @api.depends('stage_id', 'date_deadline')
    def _compute_task_status(self):
        today = fields.Date.context_today(self)
        for task in self:
            if task.stage_id and (task.stage_id.fold or getattr(task.stage_id, 'is_closed', False) or any(k in task.stage_id.name.lower() for k in ['xong', 'giao', 'hoàn thành', 'done'])):
                task.task_status_class = 'bg-success'
                task.task_status_label = 'Đã hoàn thành'
            elif task.date_deadline and task.date_deadline < today:
                task.task_status_class = 'bg-danger'
                task.task_status_label = 'Quá hạn'
            elif task.date_deadline and task.date_deadline == today:
                task.task_status_class = 'bg-warning text-dark'
                task.task_status_label = 'Hôm nay'
            else:
                task.task_status_class = ''
                task.task_status_label = ''

    @api.model
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)
        if task.nhan_vien_ids:
            task._send_assignment_email(task.nhan_vien_ids)
        return task

    def write(self, vals):
        if 'nhan_vien_ids' in vals:
            for task in self:
                old_employee_ids = task.nhan_vien_ids.ids
                res = super(ProjectTask, task).write(vals)
                new_employee_ids = task.nhan_vien_ids.ids
                added_employee_ids = list(set(new_employee_ids) - set(old_employee_ids))
                if added_employee_ids:
                    added_employees = self.env['hr.employee'].browse(added_employee_ids)
                    task._send_assignment_email(added_employees)
        
        if 'stage_id' in vals:
            for task in self:
                new_stage = self.env['project.task.type'].browse(vals['stage_id'])
                is_done_stage = new_stage.fold or \
                                getattr(new_stage, 'is_closed', False) or \
                                any(k in new_stage.name.lower() for k in ['xong', 'giao', 'hoàn thành', 'done'])
                if is_done_stage:
                    now = fields.Datetime.now()
                    vals['date_completed'] = now
                    if task.date_deadline:
                        deadline_dt = fields.Datetime.to_datetime(task.date_deadline)
                        deadline_end = deadline_dt.replace(hour=23, minute=59, second=59)
                        diff = (deadline_end - now).total_seconds() / 3600
                        if diff > 24:
                            vals['kpi_rating'] = 'a'
                        elif diff >= 0:
                            vals['kpi_rating'] = 'b'
                        elif diff > -72:
                            vals['kpi_rating'] = 'c'
                        else:
                            vals['kpi_rating'] = 'd'
                else:
                    vals['date_completed'] = False
                    vals['kpi_rating'] = False

        return super(ProjectTask, self).write(vals)

    def _send_assignment_email(self, employees):
        # Update ref to current module
        template = self.env.ref('quan_ly_cong_viec.email_template_task_assignment', raise_if_not_found=False)
        if not template:
            return
        for task in self:
            employees_with_email = employees.filtered(lambda e: e.work_email)
            if not employees_with_email:
                continue
            template.with_context(employees=employees_with_email).send_mail(
                task.id, 
                force_send=True,
                email_values={'email_to': ','.join(employees_with_email.mapped('work_email'))}
            )

    @api.model
    def _cron_send_deadline_reminders(self):
        tomorrow = fields.Date.today() + timedelta(days=1)
        tasks_to_remind = self.search([
            ('date_deadline', '=', tomorrow),
            ('stage_id.fold', '=', False),
            ('stage_id.is_closed', '=', False),
            ('stage_id.name', 'not ilike', 'xong'),
            ('stage_id.name', 'not ilike', 'hoàn thành'),
            ('stage_id.name', 'not ilike', 'đã giao'),
            ('stage_id.name', 'not ilike', 'done')
        ])
        # Update ref to current module
        template = self.env.ref('quan_ly_cong_viec.email_template_task_deadline_reminder', raise_if_not_found=False)
        if not template:
            return
        for task in tasks_to_remind:
            if task.nhan_vien_ids:
                employees_with_email = task.nhan_vien_ids.filtered(lambda e: e.work_email)
                if employees_with_email:
                    template.send_mail(
                        task.id, 
                        force_send=True,
                        email_values={'email_to': ','.join(employees_with_email.mapped('work_email'))}
                    )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and hasattr(self.project_id, 'thanh_vien_ids'):
            valid_employee_ids = self.project_id.thanh_vien_ids.ids
            if self.nhan_vien_ids:
                invalid_employees = self.nhan_vien_ids.filtered(lambda e: e.id not in valid_employee_ids)
                if invalid_employees:
                    self.nhan_vien_ids = [(3, employee.id) for employee in invalid_employees]
            return {'domain': {'nhan_vien_ids': [('id', 'in', valid_employee_ids)]}}
        else:
            return {'domain': {'nhan_vien_ids': []}}

    def action_generate_tasks_ai_from_task(self):
        project_id = self.env.context.get('default_project_id') or self.env.context.get('active_id')
        if not project_id:
            raise ValidationError("❌ Không tìm thấy Dự án gốc.")
        project = self.env['project.project'].browse(project_id)
        if not project.exists():
            raise ValidationError("❌ Dự án không tồn tại.")
        if hasattr(project, 'action_generate_tasks_ai'):
            return project.action_generate_tasks_ai()
        return False
