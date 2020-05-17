from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime




class JobPosition(models.Model):
    _name = 'job.title'
    name = fields.Char(required=True)
    department_ids = fields.Many2many('hr.department', 'hr_dep_job_rel', 'job_id', 'dep_id')
    job_code = fields.Char(string="Job Code",readonly=True ,store=True )
    has_application = fields.Boolean(string='Has Application', compute='_compute_has_application')
    job_level_ids = fields.One2many('job.level', 'job_title_id', string="Job Levels" )

    #  override create to generate job code to take first two letter and if it repated add number specific for each code
    #""" get first two letters of first two words then check if this code found before or not
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
        if vals['name']:
            job_name =  vals['name'].split()[:2]
            for initial in job_name:
                initials.append(initial[:2].upper())
            job_code = "".join(initial for initial in initials) if initials else False
            # update the old value by null to not get as a result for secound query
            self._cr.execute(" update job_title set job_code = '---' where id =  %s " ,(self.id,) )
            self._cr.execute(
                "select job_code from job_title where job_code ilike  %s or  job_code ilike  %s  order by create_date ",(job_code,str(job_code)+'\_%',))
            results = self.env.cr.fetchall()
            if results:
                if len(results)> 1:
                    last_code = list(results[len(results) - 1]) # convert to list and get last item
                    last_index=str(last_code[0])[-1:] # convert to string then get last charcter
                    vals['job_code']=job_code+'_'+str(int(last_index)+1)
                else :
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

    _sql_constraints = [('name_unique',
                         'unique(name)',
                         'The name of the Business unit must be unique!'), ]


class Department(models.Model):
    _inherit = "hr.department"
    # current_user=fields.Many2one('res.users',default=lambda self: self.env.uid)
    allow_call= fields.Boolean(string='Allow Online Call')

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
            child_department= self.env['hr.department'].search([('parent_id','=',self._origin.id),('parent_id','!=',False)])
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

class JobLevel(models.Model):
    _name = 'job.level'
    name = fields.Char(required=True)
    job_title_id = fields.Many2one('job.title', string="Job Title", required=True, ondelete='cascade')

    _sql_constraints = [('name_job_title_unique',
                         'unique(name,job_title_id)',
                         'The name of the Job Level must be unique! per Job Title.'), ]


class Job(models.Model):
    _inherit = ['hr.job']

    # def _get_default_bu(self):
    #        return self.env.ref('recruitment_ads.main_andalusia_bu', raise_if_not_found=False)

    def _get_bu_domain(self):
        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            domain=['|',('id', '=', self.env.user.business_unit_id.id), ('id','in',self.env.user.multi_business_unit_id.ids)
                 ]

        else:
            domain=[]
        return domain
    name = fields.Char(string='Job Position', required=False, index=True, translate=True, compute='_compute_job_name',
                       store=True)
    business_unit_id = fields.Many2one('business.unit', required=True, domain=lambda self: self._get_bu_domain())
    department_id = fields.Many2one('hr.department', string='Department', required=True,
                                    domain=[('parent_id', '=', False)])
    section_id = fields.Many2one('hr.department', "Section", domain=[('parent_id', '!=', False)])
    job_title_id = fields.Many2one('job.title', string='Job Title', required=True)
    job_level_id = fields.Many2one('job.level', string='Job Level', required=False)
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


    @api.model
    def create(self, vals):
        vals['last_launch_rec_date'] = datetime.today()
        return super(Job, self).create(vals)

    @api.multi
    def write(self, vals):
        user = self.env.user
        if user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') :
            if self.business_unit_id.id != user.business_unit_id.id and not self.business_unit_id.id in user.multi_business_unit_id.ids and self._context.get('allow_edit',False)== False:
                raise ValidationError("You are not allowed to edit this job")
        if user.has_group('hr_recruitment.group_hr_recruitment_user') and not user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') and self._context.get('allow_edit',False)== False:
            raise ValidationError("You are not allowed to edit this job")
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
        hired_offer = self.env['hr.offer'].search([('job_id', 'in', self.ids), ('state', '=', 'hired'),('hiring_date','!=',False)])
        for job in self:
            if job.state == 'recruit' and job.last_launch_rec_date :
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
