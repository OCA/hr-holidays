from odoo import _, api, models


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    @api.model_create_multi
    def create(self, vals_list):
        holidays = super().create(vals_list)

        auto_validate = holidays.filtered(
            lambda h: (
                h.holiday_status_id.leave_validation_type != "no_validation"
                and (
                    (
                        h.holiday_status_id.validation_type_split == "hours"
                        and not h.request_unit_hours
                        and not h.request_unit_half
                    )
                    or (
                        h.holiday_status_id.validation_type_split == "days"
                        and (h.request_unit_hours or h.request_unit_half)
                    )
                )
            )
        )

        for holiday in auto_validate:
            # As done in core, we use sudo() as the user might not have the
            # rights when creating the leave
            # https://github.com/odoo/odoo/blob/97b60952d59a57aba12b048cb4da4f41d85d2ea2/addons/hr_holidays/models/hr_leave.py#L978-L980
            holiday.sudo().action_validate()
            holiday.sudo().message_subscribe(
                partner_ids=holiday._get_responsible_for_approval().partner_id.ids
            )
            holiday.sudo().message_post(
                body=_("The time off has been automatically approved"),
                subtype_xmlid="mail.mt_comment",
            )

        return holidays
