from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_round

class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    remaining_leaves_hours = fields.Float(compute='_compute_remaining_leaves')
    remaining_leaves_days = fields.Float(compute='_compute_remaining_leaves')
    remaining_leaves_display = fields.Char('Remaining', compute='_compute_remaining_leaves_display')

    def _compute_remaining_leaves(self):
        for allocation in self:

            # Get number of days for all validated leaves filtered by employee and leave type
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', allocation.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=',  allocation.holiday_status_id.id)
            ])
            allocation.remaining_leaves_days = allocation.number_of_days - sum(leaves.mapped('number_of_days'))
            allocation.remaining_leaves_hours = allocation.number_of_hours_display - sum(leaves.mapped('number_of_hours_display'))
    
    # @api.depends('remaining_leaves_hours', 'remaining_leaves_days')
    def _compute_remaining_leaves_display(self):
        for allocation in self:
            allocation.remaining_leaves_display = '%g %s' % (
                (float_round(allocation.remaining_leaves_hours, precision_digits=2)
                if allocation.type_request_unit == 'hour'
                else float_round(allocation.remaining_leaves_days, precision_digits=2)),
                _('hours') if allocation.type_request_unit == 'hour' else _('days'))