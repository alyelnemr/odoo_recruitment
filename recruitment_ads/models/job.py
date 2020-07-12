from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class JobPosition(models.Model):
    _name = 'job.title'
    name = fields.Char(required=True)
    department_ids = fields.Many2many('hr.department', 'hr_dep_job_rel', 'job_id', 'dep_id')
    job_code = fields.Char(string="Job Code", readonly=True, store=True)
    has_application = fields.Boolean(string='Has Application', compute='_compute_has_application')
    # job_level_ids = fields.One2many('job.level', 'job_title_id', string="Job Levels")
    job_level_ids = fields.Many2many('job.level', 'hr_level_title_rel', 'job_id', 'level_id', string="Job Levels")

    #  override create to generate job code to take first two letter and if it repated add number specific for each code
    # """ get first two letters of first two words then check if this code found before or not
    # if no then  save the code if  yes the add  "_" and the seq number of code
    # """
    @api.model
    def create(self, vals):
        initials = []
        if vals['name']:
            job_name = vals['name'].split()[:2]
            for initial in job_name:
                initials.append(initial[:2].upper())
            job_code = "".join(initial for initial in initials) if initials else False
            self._cr.execute(
                "select job_code from job_title where job_code ilike  %s or  job_code ilike  %s  order by create_date ",
                (job_code, str(job_code) + '\_%',))
            results = self.env.cr.fetchall()
            if results:
                if len(results) > 1:
                    last_code = list(results[len(results) - 1])  # convert to list and get last item
                    last_index = str(last_code[0])[-1:]  # convert to string then get last charcter
                    vals['job_code'] = job_code + '_' + str(int(last_index) + 1)
                else:
                    vals['job_code'] = job_code + '_' + str(1)
            else:
                vals['job_code'] = job_code
        return super(JobPosition, self).create(vals)

    @api.multi
    def write(self, vals):
        initials = []
        if vals.get('name', False):
            job_name = vals['name'].split()[:2]
            for initial in job_name:
                initials.append(initial[:2].upper())
            job_code = "".join(initial for initial in initials) if initials else False
            # update the old value by null to not get as a result for secound query
            self._cr.execute(" update job_title set job_code = '---' where id =  %s ", (self.id,))
            self._cr.execute(
                "select job_code from job_title where job_code ilike  %s or  job_code ilike  %s  order by create_date ",
                (job_code, str(job_code) + '\_%',))
            results = self.env.cr.fetchall()
            if results:
                if len(results) > 1:
                    last_code = list(results[len(results) - 1])  # convert to list and get last item
                    last_index = str(last_code[0])[-1:]  # convert to string then get last charcter
                    vals['job_code'] = job_code + '_' + str(int(last_index) + 1)
                else:
                    vals['job_code'] = job_code + '_' + str(1)
            else:
                vals['job_code'] = job_code
        return super(JobPosition, self).write(vals)

    def _compute_has_application(self):
        title_id = self.id
        if self.env['hr.applicant'].search([('job_id.job_title_id.id', '=', title_id)], limit=1):
            self.has_application = True

    # _sql_constraints = [
    #     ('job_title_uniq',
    #      'unique(name)',
    #      'Job title entered before, Job title must be unique.'),
    #     ('job_code_uniq',
    #      'unique(job_code)',
    #      'Job Code entered before, Job Code must be unique.'),
    # ]

    _sql_constraints = [
        ('job_code_uniq',
         'unique(job_code)',
         'Job Code entered before, Job Code must be unique.'),
    ]


class BusinessUnit(models.Model):
    _name = 'business.unit'
    name = fields.Char(required=True)
    job_dep_ids = fields.One2many('hr.department', 'business_unit_id')
    bu_location = fields.Selection([('egypt', 'Egypt'), ('ksa', 'KSA')], string='Location', default='egypt')

    _sql_constraints = [('name_unique',
                         'unique(name)',
                         'The name of the Business unit must be unique!'), ]


class Department(models.Model):
    _inherit = "hr.department"
    # current_user=fields.Many2one('res.users',default=lambda self: self.env.uid)
    allow_call = fields.Boolean(string='Allow Online Call')

    def _get_default_bu(self):
        if self.parent_id:
            return self.parent_id.business_unit_id
        else:
            return self.env.ref('recruitment_ads.main_andalusia_bu', raise_if_not_found=False)

    business_unit_id = fields.Many2one('business.unit', required=True, default=_get_default_bu)
    job_title_ids = fields.Many2many('job.title', 'hr_dep_job_rel', 'dep_id', 'job_id', string='Job Titles')

    @api.constrains('business_unit_id', 'parent_id')
    def check_business_unit(self):
        for dep in self:
            if dep.parent_id.business_unit_id:
                if dep.business_unit_id != dep.parent_id.business_unit_id:
                    raise ValidationError(
                        _("You can't create department with BU different from its parent department "))

    _sql_constraints = [('name_business_unit_id_unique',
                         'unique(name,business_unit_id)',
                         'The name of the department must be unique per business unit!'), ]

    @api.onchange('allow_call')
    def _get_allow_call(self):
        if not self.parent_id:
            child_department = self.env['hr.department'].search(
                [('parent_id', '=', self._origin.id), ('parent_id', '!=', False)])
            if child_department:
                for child in child_department:
                    child.write({'allow_call': self.allow_call})

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.allow_call = self.parent_id.allow_call
            self.business_unit_id = self.parent_id.business_unit_id

    @api.model
    def create(self, vals):
        if vals['parent_id']:
            parent_department = self.env['hr.department'].search([('id', '=', vals['parent_id'])])
            if parent_department:
                vals['allow_call'] = parent_department.allow_call
                vals['business_unit_id'] = parent_department.business_unit_id.id

        return super(Department, self).create(vals)

    @api.multi
    def write(self, vals):
        user = self.env.user
        if user.has_group('hr_recruitment.group_hr_recruitment_user') and not user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') and not user.has_group(
            'recruitment_ads.group_hr_recruitment_coordinator') and self._context.get('allow_edit', False) == False:
            raise ValidationError("You are not allowed to edit this job")
        return super(Department, self).write(vals)


class JobLevel(models.Model):
    _name = 'job.level'

    name = fields.Char(required=True)
    # job_title_id = fields.Many2one('job.title', string="Job Title", required=False, ondelete='cascade')
    job_title_ids = fields.Many2many('job.title', 'hr_level_title_rel', 'level_id', 'job_id', string="Job title",
                                     required=True)
    weight = fields.Integer(string="Level weight", required=True)
    cv = fields.Integer(string="CVs", required=True)

    _sql_constraints = [('name_job_title_unique',
                         'unique(name)',
                         'The name of the Job Level must be unique!'), ]

    @api.model
    def create(self, vals):
        if vals['weight'] < 1:
            raise ValidationError(_("The field 'Level weight' must be greater than 0"))
        if vals['cv'] < 1:
            raise ValidationError(_("The field 'CV' must be greater than 0"))
        res = super(JobLevel, self).create(vals)
        # add new inserted job level here in (HR Policy, offer and hire levels)
        # to be always synced with HR Policy
        hr_policy = self.env['hr.policy'].search([('hr_policy_type', '=', 'offer_and_hire')], limit=1)
        self.env['hr.policy.offer.and.hire.level'].create({
                    'level': res.id,
                    'offer': 0,
                    'hire': 0,
                    'total': 0,
                    'hr_policy': hr_policy.id
                })

        return res

    @api.multi
    def write(self, vals):
        for level in self:
            if level.weight < 1 and not vals.get('weight', False):
                raise ValidationError(_("The field 'Level weight' must be greater than 0"))
            if vals.get('weight', False):
                if vals['weight'] < 1:
                    raise ValidationError(_("The field 'Level weight' must be greater than 0"))
            if level.cv < 1 and not vals.get('cv', False):
                raise ValidationError(_("The field 'cv' must be greater than 0"))
            if vals.get('cv', False):
                if vals['cv'] < 1:
                    raise ValidationError(_("The field 'CV' must be greater than 0"))
        return super(JobLevel, self).write(vals)


class Job(models.Model):
    _inherit = ['hr.job']

    # def _get_default_bu(self):
    #        return self.env.ref('recruitment_ads.main_andalusia_bu', raise_if_not_found=False)
    _sql_constraints = [
        ('name_company_uniq', 'CHECK(1=1)',
         'The name of the job position must be unique per department and section in company!'),
    ]

    @api.constrains('name', 'company_id', 'department_id', 'section_id')
    def _check_name_company_section_uniq(self):
        for job in self:
            exist_job = job.search([
                ('name', '=', job.name),
                ('company_id', '=', job.company_id.id or False),
                ('department_id', '=', job.department_id.id or False),
                ('section_id', '=', job.section_id.id or False),
            ])
            if exist_job and job.id not in exist_job.ids:
                raise ValidationError(
                    _('The name of the job position must be unique per department and section in company!'))

    def _get_bu_domain(self):
        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            domain = ['|', ('id', '=', self.env.user.business_unit_id.id),
                      ('id', 'in', self.env.user.multi_business_unit_id.ids)
                      ]

        else:
            domain = []
        return domain

    name = fields.Char(string='Job Position', required=False, index=True, translate=True, compute='_compute_job_name',
                       store=True)
    business_unit_id = fields.Many2one('business.unit', required=True, domain=lambda self: self._get_bu_domain())
    department_id = fields.Many2one('hr.department', string='Department', required=True,
                                    domain=[('parent_id', '=', False)])
    section_id = fields.Many2one('hr.department', "Section", domain=[('parent_id', '!=', False)])
    job_title_id = fields.Many2one('job.title', string='Job Title', required=True)
    job_level_id = fields.Many2one('job.level', string='Job Level', required=False)
    # , domain = lambda self: self.job_title_level_domain()
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    other_recruiters_ids = fields.Many2many('res.users', string="Other Recruiters")
    remaining_vacancies = fields.Integer(string='Remaining Vacancies', compute='_compute_remaining_vacancies',
                                         help='Number of vacancies needed during the recruitment phase.')
    no_of_hired_applicants = fields.Integer(string='Hired Applicants', compute='_compute_remaining_vacancies',
                                            help='Number of hired applicants for this job position during recruitment phase.')
    last_launch_rec_date = fields.Date(string='Recruitment Launch Date',
                                       help="Technical field to catch the starting date of the last recruitment phase")
    scale_from = fields.Float(string='Salary Scale From')
    scale_to = fields.Float(string='Salary Scale To')
    edited_recruiter_responsible = fields.Many2one('res.users')
    removed_recruiter_responsible = fields.Many2one('res.users')

    @api.model
    def create(self, vals):
        vals['last_launch_rec_date'] = datetime.today()
        res = super(Job, self).create(vals)
        res.job_assignment(res, action='create')
        return res

    @api.multi
    def write(self, vals):
        user = self.env.user
        if user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            if self.business_unit_id.id != user.business_unit_id.id and not self.business_unit_id.id in user.multi_business_unit_id.ids and self._context.get(
                    'allow_edit', False) == False:
                raise ValidationError("You are not allowed to edit this job")
        if user.has_group('hr_recruitment.group_hr_recruitment_user') and not user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') and not user.has_group(
            'recruitment_ads.group_hr_recruitment_coordinator') and self._context.get('allow_edit', False) == False:
            raise ValidationError("You are not allowed to edit this job")
        if vals.get('user_id', False) or vals.get('other_recruiters_ids', False):
            self.job_assignment(vals, action='write')
        return super(Job, self).write(vals)

    @api.one
    @api.depends('job_title_id.name', 'job_level_id.name')
    def _compute_job_name(self):
        self.name = " - ".join([name for name in (self.job_title_id.name, self.job_level_id.name) if name])

    @api.multi
    def set_recruit(self):
        for record in self:
            no_of_recruitment = 1 if record.no_of_recruitment == 0 else record.no_of_recruitment
            record.write({'state': 'recruit', 'no_of_recruitment': no_of_recruitment})
            if record.state == "recruit":
                record.last_launch_rec_date = datetime.today()
        return True

    @api.multi
    def _compute_remaining_vacancies(self):
        hired_offer = self.env['hr.offer'].search(
            [('job_id', 'in', self.ids), ('state', '=', 'hired'), ('hiring_date', '!=', False)])
        for job in self:
            if job.state == 'recruit' and job.last_launch_rec_date:
                filter_by = lambda d: datetime.strptime(d.hiring_date, DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime(
                    job.last_launch_rec_date, DEFAULT_SERVER_DATE_FORMAT) and d.job_id == job
                hired_count = len(hired_offer.filtered(filter_by))
                job.no_of_hired_applicants = hired_count
                rem_vac = job.no_of_recruitment - hired_count
                if rem_vac < 0:
                    job.remaining_vacancies = 0
                else:
                    job.remaining_vacancies = rem_vac
            else:
                job.no_of_hired_applicants = 0
                job.remaining_vacancies = 0

    @api.onchange('job_title_id')
    def onchange_job_title_id(self):
        self.job_level_id = False

    @api.onchange('business_unit_id')
    def onchange_business_unit(self):
        self.department_id = False
        self.job_title_id = False
        self.job_level_id = False
        self.section_id = False

    @api.onchange('department_id')
    def onchange_department_id(self):
        self.job_title_id = False
        self.job_level_id = False
        if self.department_id != self.section_id.parent_id:
            self.section_id = False

    def job_assignment(self, vals, action):
        rec_user = ""
        rec_other_user = ""
        user_obj = self.env['res.users']
        old_rec = ""
        old_other = ""
        if action == 'create':
            rec_user = vals.user_id
            rec_other_user = vals.other_recruiters_ids
            old_rec = []
            old_other = []
        elif action == 'write':
            rec_user = user_obj.browse(vals.get('user_id', False))
            rec_other_user = user_obj.browse(vals.get('other_recruiters_ids', False)[0][2]) if vals.get(
                'other_recruiters_ids', False) else ""
            old_rec = self.user_id
            old_other = self.other_recruiters_ids
        if rec_user or rec_other_user or old_rec or old_other:
            added_rec_users_list = []
            removed_rec_users_list = []
            if rec_user:
                added_rec_users_list.append(rec_user)
                removed_rec_users_list.append(old_rec) if old_rec else False
            if rec_other_user or old_other:
                for m in rec_other_user:
                    if m not in old_other and m not in added_rec_users_list:
                        added_rec_users_list.append(m)
                for m in old_other:
                    if m not in rec_other_user and m not in removed_rec_users_list:
                        removed_rec_users_list.append(m)
            intersection = [x for x in added_rec_users_list if x in removed_rec_users_list] + \
                           [x for x in removed_rec_users_list if x in added_rec_users_list]
            if added_rec_users_list:
                for user in added_rec_users_list:
                    if user not in intersection:
                        self.write({'edited_recruiter_responsible': user[0].id})
                        self.send_mail_job_assignment_template()
            if removed_rec_users_list:
                for user in removed_rec_users_list:
                    if user not in intersection:
                        self.write({'removed_recruiter_responsible': user[0].id})
                        self.send_mail_job_not_assigned_template()

    @api.multi
    def send_mail_job_assignment_template(self):
        # Find the e-mail template
        template = self.env.ref('recruitment_ads.job_assignment_email_template')
        # Send out the e-mail template to the user
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.multi
    def send_mail_job_not_assigned_template(self):
        # Find the e-mail template
        template = self.env.ref('recruitment_ads.job_not_assignment_email_template')
        # Send out the e-mail template to the user
        self.env['mail.template'].browse(template.id).send_mail(self.id)
