from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    pending_inbox_id = fields.Many2one(
        comodel_name="project.pending.inbox",
        string="Origen (Pendiente)",
        index=True,
        help="Origen del registro desde el buzón de pendientes indefinidos.",
    )


class ProjectProject(models.Model):
    _inherit = "project.project"

    pending_inbox_id = fields.Many2one(
        comodel_name="project.pending.inbox",
        string="Origen (Pendiente)",
        index=True,
        help="Origen del registro desde el buzón de pendientes indefinidos.",
    )


