from odoo import api, models


class HrLeave(models.Model):
    _name = "hr.leave"
    _inherit = ["hr.leave", "tier.validation"]
    _tier_validation_manual_config = False
    _state_field = "state"
    _state_from = ["confirm"]
    _state_to = ["validate"]
    _cancel_state = "refuse"

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        records = super().create(vals_list)

        # Request validation for records that need tier validation and are in confirm state
        for record in records:
            if (
                record.holiday_status_id.leave_validation_type == "tier_validation"
                and record.state == "confirm"
                and record.need_validation
            ):
                record.request_validation()

        return records

    def action_confirm(self):
        """Override to request tier validation on confirm if needed."""
        res = super().action_confirm()

        for rec in self:
            if (
                rec.holiday_status_id.leave_validation_type == "tier_validation"
                and rec.need_validation
            ):
                rec.request_validation()

        return res

    # ### Tier validation waiting Overrides ###

    @api.depends("review_ids.status", "holiday_status_id.leave_validation_type")
    def _compute_need_validation(self):
        """Override to check for tier validation only if leave type validation
        is set to tier_validation."""
        for rec in self:
            if rec.holiday_status_id.leave_validation_type == "tier_validation":
                # Only use tier validation logic for tier validation leave types
                return super()._compute_need_validation()
            else:
                # For other validation types, no tier validation is needed
                rec.need_validation = False

    def _get_validation_exceptions(self, extra_domain=None, add_base_exceptions=True):
        """Add fields to tier validation exceptions."""
        res = super()._get_validation_exceptions(extra_domain, add_base_exceptions)
        res.extend(
            ["state", "meeting_id", "first_approver_id", "second_approver_id", "active"]
        )
        return res

    def _check_state_conditions(self, vals):
        """Override to handle state conditions to respect
        skip_check_state_condition context."""
        if self.env.context.get("skip_check_state_condition", False):
            return False

        return super()._check_state_conditions(vals)

    def _validate_tier(self, tiers):
        """Validate leave if all reviews are approved."""

        res = super()._validate_tier(tiers)
        if all(review.status == "approved" for review in self.review_ids):

            # Trigger leave validation if all reviews are approved
            self.with_context(
                mail_activity_automation_skip=True,
                skip_check_state_condition=True,
            ).action_validate()

        return res

    def _rejected_tier(self, tiers):
        """Override to handle tier rejection logic."""

        res = super()._rejected_tier(tiers)
        # Trigger leave refusal if the tier is rejected
        self.with_context(skip_check_state_condition=True).action_refuse()

        return res

    def _notify_review_available(self, tier_reviews):
        if hasattr(self, "message_post") and hasattr(self, "message_subscribe"):
            for rec in self.sudo():
                # Limit the message dest. to the users that have to do the next review
                users_to_notify = tier_reviews.filtered(
                    lambda r: r.definition_id.notify_on_pending
                    and r.res_id == rec.id  # and r.validation_status == "pending"
                ).mapped("reviewer_ids")

                # Subscribe reviewers and notify
                if len(users_to_notify) > 0:
                    rec.message_subscribe(
                        partner_ids=users_to_notify.mapped("partner_id").ids,
                        subtype_ids=self.env.ref(
                            self._get_requested_notification_subtype()
                        ).ids,
                    )
                    # Do not subscribe recipients to avoid future notifications
                    rec.with_context(mail_post_autofollow=False).message_post(
                        subtype_xmlid=self._get_requested_notification_subtype(),
                        body=rec._notify_requested_review_body(),
                        partner_ids=users_to_notify.mapped("partner_id").ids,
                        message_type="email",
                    )

    def _notify_get_recipients_groups(self, msg_vals=None):
        """Disable direct action links, force user to go to the leave request page
        The main goal is to avoid users to use upstream validation actions and
        bypass tier validation

        TODO:
        - Disable controllers of the upstream validation/refusal actions
        """

        # Get the default groups from parent
        groups = super()._notify_get_recipients_groups(msg_vals)

        # Update all groups to have empty actions list
        for _group_name, _group_func, group_data in groups:
            group_data["actions"] = []

        return groups
