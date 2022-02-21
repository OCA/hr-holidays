# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

TYPE_SELECTION = [
    ("leave_request", "Leave Request"),
    ("leave_allocation", "Leave Allocation"),
]
ONDELETE_SELECTION = {
    "leave_request": "set default",
    "leave_allocation": "set default",
}

_logger = logging.getLogger(__name__)


class HrEmployeeHour(models.Model):
    _inherit = "hr.employee.hour"

    type = fields.Selection(
        selection_add=TYPE_SELECTION, ondelete=ONDELETE_SELECTION
    )
    state = fields.Selection(
        [
            ('draft', 'To Submit'),
            ('cancel', 'Cancelled'),
            ('confirm', 'To Approve'),
            ('refuse', 'Refused'),
            ('validate1', 'Second Approval'),
            ('validate', 'Approved'),
        ],
        "State",
    )

    @api.model
    def search_allocations_domain(
        self, employee, date_from=None, date_to=fields.Date().today()
    ):
        """ Search filter rules for allocations """
        if not date_from:
            date_from = employee.first_contract_date
        return [
            ("employee_id", "=", employee.id),
            ("state", "not in", ("draft", "cancel", "refuse")),
            ("date_from", ">=", date_from),
            "|",
            ("date_to", "=", False),
            ("date_to", "<=", date_to),
        ]

    @api.model
    def search_requests_domain(
        self, employee, date_from=None, date_to=fields.Date().today()
    ):
        """ Search filter rules for requests """
        if not date_from:
            date_from = employee.first_contract_date
        return [
            ("employee_id", "=", employee.id),
            ("state", "not in", ("draft", "cancel", "refuse")),
            ("date_from", ">=", date_from),
            ("date_to", "<=", date_to),
        ]

    @api.model
    def _prepare_leave_allocation_values(
        self, employee, date_from=None, date_to=None
    ):
        """ Retrieve leave allocations values

        :param employee: an employee record
        :param date_from: a datetime.date object (default first contract date, included)
        :param date_to: a datetime.date object (default today, included)
        """
        if not date_from:
            date_from = employee.first_contract_date
        if not date_to:
            date_to = fields.Date().today().replace(day=31, month=12)
        ir_model = self.env["ir.model"]
        hla_model = self.env["hr.leave.allocation"]
        hla_model_id = ir_model.search([("model", "=", hla_model._name)])
        search_domain = self.search_allocations_domain(
            employee, date_from, date_to
        )
        allocations = hla_model.with_context(active_test=False).search(
            search_domain
        )
        values_list = []
        for allocation in allocations:
            days_qty = allocation.number_of_days
            hours_qty = allocation.number_of_hours_display
            values_list.append(
                {
                    "date": allocation.date_from,
                    "name": allocation.holiday_status_id.name,
                    "active": allocation.holiday_status_id.active,
                    "employee_id": employee.id,
                    "model_id": hla_model_id.id,
                    "res_id": allocation.id,
                    "type": "leave_allocation",
                    "hours_qty": hours_qty,
                    "days_qty": days_qty,
                    "state": allocation.state,
                }
            )
        return values_list

    @api.model
    def _prepare_leave_request_values(
        self, employee, date_from=None, date_to=None
    ):
        """ Retrieve leave requests values

        :param employee: an employee record
        :param date_from: a datetime.date object (default first contract date, included)
        :param date_to: a datetime.date object (default today, included)
        """
        if not date_from:
            date_from = employee.first_contract_date
        if not date_to:
            date_to = fields.Date().today().replace(day=31, month=12)
        ir_model = self.env["ir.model"]
        hl_model = self.env["hr.leave"]
        hl_model_id = ir_model.search([("model", "=", hl_model._name)])
        search_domain = self.search_requests_domain(
            employee, date_from, date_to
        )
        requests = hl_model.with_context(active_test=False).search(
            search_domain
        )
        values_list = []
        for request in requests:
            days_qty = request.number_of_days
            hours_qty = request.number_of_hours_display
            holiday_status_id = request.holiday_status_id
            values_list.append(
                {
                    "date": request.date_from,
                    "name": holiday_status_id.name,
                    "active": holiday_status_id.active,
                    "employee_id": employee.id,
                    "model_id": hl_model_id.id,
                    "res_id": request.id,
                    "type": "leave_request",
                    "hours_qty": hours_qty,
                    "days_qty": days_qty,
                    "state": request.state,
                    "unplanned": holiday_status_id.allocation_type == "no",
                }
            )
        return values_list

    def _prepare_values(self, employee, date_from=None, date_to=None):
        values_list = super()._prepare_values(employee, date_from, date_to)
        if not date_from:
            date_from = employee.first_contract_date
        # For leaves and holidays, we need to have a whole year view
        date_to = fields.Date().today().replace(day=31, month=12)
        leave_alloc_values = self._prepare_leave_allocation_values(
            employee, date_from, date_to
        )
        leave_request_values = self._prepare_leave_request_values(
            employee, date_from, date_to
        )
        return values_list + leave_request_values + leave_alloc_values
