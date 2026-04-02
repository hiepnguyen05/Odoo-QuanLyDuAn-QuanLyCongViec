# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext
import time

class SubtaskHrm(models.Model):
    _name = 'quan_ly_cong_viec.subtask'
    _description = 'Dummy Model to fix Registry'

class TaskBaseHrm(models.Model):
    _name = 'quan_ly_cong_viec.task'
    _description = 'Dummy Model to fix Registry 2'

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    # Ghi đè stage_id để thêm group_expand, giúp luôn hiển thị đủ 5 cột Kanban chuẩn
    stage_id = fields.Many2one(
        'project.task.type', 
        string='Giai đoạn', 
        ondelete='restrict', 
        tracking=True, 
        index=True, 
        copy=False,
        group_expand='_read_group_stage_ids'
    )
    
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
        store=True,
        group_operator="avg"
    )
    
    task_status_class = fields.Char(compute='_compute_task_status', store=False)
    task_status_label = fields.Char(compute='_compute_task_status', store=False)

    task_summary = fields.Text(
        string='Tóm tắt công việc (AI)',
        help='Bản tóm tắt ngắn gọn nội dung công việc do AI thực hiện'
    )

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
            if not task.stage_id:
                task.task_status_label = ''
                task.task_status_class = ''
                continue

            # Nhãn luôn là tên của Stage (Trạng thái nào nhãn đấy)
            task.task_status_label = task.stage_id.name
            stage_name_lower = task.stage_id.name.lower()

            # Xác định màu sắc dựa trên tính chất trạng thái
            if any(k in stage_name_lower for k in ['hủy', 'cancel']):
                task.task_status_class = 'bg-dark'
            elif task.stage_id.fold or getattr(task.stage_id, 'is_closed', False) or \
                 any(k in stage_name_lower for k in ['xong', 'giao', 'hoàn thành', 'done']):
                task.task_status_class = 'bg-success'
            elif task.date_deadline and task.date_deadline < today:
                task.task_status_class = 'bg-danger'
            elif task.date_deadline and task.date_deadline == today:
                task.task_status_class = 'bg-warning text-dark'
            else:
                task.task_status_class = 'bg-info'

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
        
        tasks_to_notify = self.env['project.task']
        if 'stage_id' in vals:
            new_stage = self.env['project.task.type'].browse(vals['stage_id'])
            is_done_stage = (new_stage.fold or getattr(new_stage, 'is_closed', False) or \
                             any(k in new_stage.name.lower() for k in ['xong', 'giao', 'hoàn thành', 'done'])) and \
                             not any(k in new_stage.name.lower() for k in ['hủy', 'cancel'])

            for task in self:
                # Chỉ xử lý nếu có sự chuyển trạng thái mới thực sự
                if task.stage_id != new_stage:
                    if is_done_stage:
                        # Kiểm tra xem trước đó đã xong chưa để tránh gửi email lặp lại
                        was_done = (task.stage_id.fold or getattr(task.stage_id, 'is_closed', False) or \
                                   any(k in task.stage_id.name.lower() for k in ['xong', 'giao', 'hoàn thành', 'done'])) and \
                                   not any(k in task.stage_id.name.lower() for k in ['hủy', 'cancel'])
                        
                        if not was_done:
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
                            
                            tasks_to_notify |= task
                    else:
                        vals['date_completed'] = False
                        vals['kpi_rating'] = False

        res = super(ProjectTask, self).write(vals)
        
        # Gửi email sau khi dữ liệu đã được lưu vào database
        if tasks_to_notify:
            tasks_to_notify.sudo()._send_completion_email()
            
        return res

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

    def _send_completion_email(self):
        """Gửi email thông báo khi công việc hoàn thành"""
        template = self.env.ref('quan_ly_cong_viec.email_template_task_completed', raise_if_not_found=False)
        if not template:
            return
        for task in self:
            # Gửi cho Quản lý dự án (nếu có email)
            recipient = task.project_id.user_id.email
            if recipient:
                template.send_mail(task.id, force_send=True)

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

    def action_summarize_task_ai(self):
        """Gọi Gemini AI để tóm tắt nội dung công việc"""
        self.ensure_one()
        
        # 1. Lấy nội dung đầu vào (dọn dẹp HTML từ Description, nếu không có lấy Name)
        raw_text = self.description or self.name
        if not raw_text:
            raise ValidationError("❌ Cần có nội dung Mô tả để AI có thể tóm tắt.")
            
        # Dọn dẹp HTML để AI đọc text thuần tốt hơn
        input_text = html2plaintext(raw_text).strip() if self.description else raw_text

        # 2. Lấy API Key
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini.api_key')
        if not api_key:
            raise ValidationError("❌ Chưa cấu hình API Key cho Gemini AI trong 'Thông số hệ thống'.")

        # Danh sách model thử lần lượt (từ mới nhất đến cũ nhất, đã loại bỏ gemini-pro bị Google ngừng hỗ trợ)
        model_candidates = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
        ]
        
        prompt = f"""
        Nhiệm vụ: Tóm tắt nội dung công việc sau đây một cách cực kỳ ngắn gọn, súc tích trong 1 đến 2 câu. 
        Đảm bảo giữ lại các mốc thời gian hoặc yêu cầu quan trọng nhất nếu có.
        
        Nội dung cần tóm tắt:
        ---
        {input_text}
        ---
        Kết quả trả về chỉ bao gồm văn bản tóm tắt, không thêm bất kỳ dẫn giải nào khác.
        """
        
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            import requests
            import json
            
            last_error = None
            response = None
            for model_name in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
                except Exception as e:
                    last_error = str(e)
                    response = None
                    continue

                if response.status_code == 200:
                    break  # OK
                elif response.status_code == 429:
                    last_error = f"Model {model_name} hết hạn mức (429)."
                    time.sleep(5)
                    continue
                elif response.status_code == 404:
                    last_error = f"Model {model_name} không tìm thấy (404)."
                    continue
                else:
                    last_error = f"Lỗi từ {model_name}: {response.status_code}"
                    continue

            if not response or response.status_code != 200:
                raise ValidationError(_(
                    "Tất cả các model AI đều đang bận hoặc hết hạn mức.\n\n"
                    "Giải pháp:\n"
                    "1. Vui lòng đợi khoảng 1 phút rồi nhấn lại nút Tóm tắt.\n"
                    "2. Hoặc cấu hình API Key mới trong Thông số hệ thống.\n\n"
                    f"Chi tiết: {last_error}"
                ))

            result = response.json()
            if 'candidates' in result and result['candidates']:
                summary = result['candidates'][0]['content']['parts'][0]['text']
                self.task_summary = summary.strip()
                return
            else:
                raise ValidationError(_("AI trả về kết quả rỗng (candidates list empty)."))
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Có lỗi bất ngờ khi gọi AI: {str(e)}")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        Luôn hiển thị 5 cột trạng thái chuẩn (Mới, Đang thực hiện, Tạm dừng, 
        Đã hoàn thành, Đã hủy) trong màn hình Kanban, kể cả khi cột trống.
        """
        stage_xml_ids = [
            'quan_ly_du_an.project_stage_new',
            'quan_ly_du_an.project_stage_in_progress',
            'quan_ly_du_an.project_stage_paused',
            'quan_ly_du_an.project_stage_done',
            'quan_ly_du_an.project_stage_cancelled',
        ]
        
        # Tìm các stage dựa trên XML ID đã khai báo ở module quan_ly_du_an
        standard_stages = self.env['project.task.type']
        for xml_id in stage_xml_ids:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                standard_stages |= stage
        
        # Trả về tập hợp các stage chuẩn để Odoo vẽ cột
        return standard_stages

    def action_view_project_tasks(self):
        """Trả về action hiển thị danh sách công việc của dự án này"""
        self.ensure_one()
        return {
            'name': _('Công việc của dự án: %s') % self.project_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
            'target': 'current',
        }
