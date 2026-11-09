# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class HrLeaveAllocationGenerateMultiWizard(models.TransientModel):
    _inherit = "hr.leave.allocation.generate.multi.wizard"

    allocation_mode = fields.Selection(
        selection_add=[("domain", "By Domain")], ondelete={"domain": "set default"}
    )
    domain = fields.Char(
        string="Employee Domain",
        help="Domain to filter employees. Example: [('job_id.name', '=', 'Manager')]",
        default="[]",
    )

    def _get_employees_from_allocation_mode(self):
        self.ensure_one()
        if self.allocation_mode == "domain":
            domain = safe_eval(self.domain or "[]")
            return self.env["hr.employee"].search(domain)
        return super()._get_employees_from_allocation_mode()
