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
    
    task_status_class = fields.Char(compute='_compute_task_status', store=False)
    task_status_label = fields.Char(compute='_compute_task_status', store=False)

    # --- KPI Automation Fields ---
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

    # ==================== OVERRIDE METHODS ====================
    
    @api.model
    def create(self, vals):
        """Override create to send email notification on initial assignment"""
        task = super(ProjectTask, self).create(vals)
        if task.nhan_vien_ids:
            task._send_assignment_email(task.nhan_vien_ids)
        return task

    def write(self, vals):
        """
        Ghi đè hàm write để bắt sự kiện thay đổi Stage -> Tính KPI
        Và bắt sự kiện giao việc -> Gửi mail thông báo
        """
        # --- Logic Gửi mail thông báo (Mức 2) ---
        if 'nhan_vien_ids' in vals:
            for task in self:
                # Lấy danh sách ID nhân viên trước khi update
                old_employee_ids = task.nhan_vien_ids.ids
                
                # Thực hiện ghi đè để lấy dữ liệu mới
                res = super(ProjectTask, task).write(vals)
                
                # Tìm ra những nhân viên mới được thêm vào (mới giao việc)
                new_employee_ids = task.nhan_vien_ids.ids
                added_employee_ids = list(set(new_employee_ids) - set(old_employee_ids))
                
                if added_employee_ids:
                    added_employees = self.env['hr.employee'].browse(added_employee_ids)
                    task._send_assignment_email(added_employees)
            
            # Nếu đã xử lý write ở trên rồi thì return True luôn để tránh gọi super lần nữa bên dưới
            # Tuy nhiên để an toàn và giữ flow KPI bên dưới, ta chỉ xử lý logic gửi mail ở đây
            # và để flow tiếp tục xuống dưới.
        
        # --- Logic KPI (Đã có sẵn) ---
        # Nếu có cập nhật Stage (kéo thả Kanban hoặc chọn trên Form)
        if 'stage_id' in vals:
            for task in self:
                new_stage = self.env['project.task.type'].browse(vals['stage_id'])
                
                # Kiểm tra xem Stage mới có phải là Stage "Đóng" (Hoàn thành) không
                is_done_stage = new_stage.fold or \
                                getattr(new_stage, 'is_closed', False) or \
                                any(k in new_stage.name.lower() for k in ['xong', 'giao', 'hoàn thành', 'done'])
                
                # Nếu chuyển từ trạng thái chưa xong -> Xong
                if is_done_stage:
                    # 1. Ghi nhận thời gian hoàn thành
                    now = fields.Datetime.now()
                    vals['date_completed'] = now
                    
                    # 2. Tính toán KPI nếu có Deadline
                    if task.date_deadline:
                        deadline_dt = fields.Datetime.to_datetime(task.date_deadline)
                        # Chuyển deadline sang cuối ngày (23:59:59) để công bằng
                        deadline_end = deadline_dt.replace(hour=23, minute=59, second=59)
                        
                        diff = (deadline_end - now).total_seconds() / 3600 # Số giờ chênh lệch
                        
                        if diff > 24: # Xong trước 1 ngày trở lên
                            vals['kpi_rating'] = 'a'
                        elif diff >= 0: # Xong đúng hạn (trong vòng 24h trước deadline)
                            vals['kpi_rating'] = 'b'
                        elif diff > -72: # Trễ dưới 3 ngày (72h)
                            vals['kpi_rating'] = 'c'
                        else: # Trễ trên 3 ngày
                            vals['kpi_rating'] = 'd'
                
                # Nếu kéo ngược từ Xong về Chưa Xong -> Reset KPI (tùy chọn)
                else:
                    vals['date_completed'] = False
                    vals['kpi_rating'] = False

        return super(ProjectTask, self).write(vals)

    def _send_assignment_email(self, employees):
        """Hàm phụ trợ gửi email cho danh sách nhân viên"""
        template = self.env.ref('quan_ly_du_an.email_template_task_assignment', raise_if_not_found=False)
        if not template:
            return
            
        for task in self:
            # Lọc ra những nhân viên có email công việc
            employees_with_email = employees.filtered(lambda e: e.work_email)
            if not employees_with_email:
                continue
                
            # Gửi mail (force_send=True để gửi ngay lập tức thay vì đợi cron)
            # Ta tạo một bản sao template để override email_to cho từng nhóm giao việc
            template.with_context(employees=employees_with_email).send_mail(
                task.id, 
                force_send=True,
                email_values={'email_to': ','.join(employees_with_email.mapped('work_email'))}
            )

    @api.model
    def _cron_send_deadline_reminders(self):
        """Hàm chạy định kỳ để nhắc nhở các task sắp đến hạn (Mức 2)"""
        # Tìm các task chưa xong và có hạn chót là ngày mai
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
        
        template = self.env.ref('quan_ly_du_an.email_template_task_deadline_reminder', raise_if_not_found=False)
        if not template:
            return
            
        for task in tasks_to_remind:
            if task.nhan_vien_ids:
                # Gửi mail cho tất cả nhân viên thực hiện có email
                employees_with_email = task.nhan_vien_ids.filtered(lambda e: e.work_email)
                if employees_with_email:
                    template.send_mail(
                        task.id, 
                        force_send=True,
                        email_values={'email_to': ','.join(employees_with_email.mapped('work_email'))}
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
