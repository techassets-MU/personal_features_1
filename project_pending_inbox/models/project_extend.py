from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    pending_inbox_id = fields.Many2one(
        comodel_name="project.pending.inbox",
        string="Origen (Pendiente)",
        index=True,
        help="Origen del registro desde el buzón de pendientes indefinidos.",
    )

    def write(self, vals):
        new_name = vals.get("name")
        res = super().write(vals)
        if new_name and not self.env.context.get("skip_task_sync"):
            for task in self:
                if task.pending_inbox_id:
                    task.pending_inbox_id.with_context(skip_pending_sync=True).write({"name": new_name})
        # Archivado bidireccional
        if "active" in vals and not self.env.context.get("skip_task_archive_sync"):
            for task in self:
                if task.pending_inbox_id:
                    task.pending_inbox_id.with_context(skip_pending_archive_sync=True).write({"active": vals.get("active")})
        return res


class ProjectProject(models.Model):
    _inherit = "project.project"

    pending_inbox_id = fields.Many2one(
        comodel_name="project.pending.inbox",
        string="Origen (Pendiente)",
        index=True,
        help="Origen del registro desde el buzón de pendientes indefinidos.",
    )

    def write(self, vals):
        new_name = vals.get("name")
        res = super().write(vals)
        if new_name and not self.env.context.get("skip_project_sync"):
            for project in self:
                if project.pending_inbox_id:
                    project.pending_inbox_id.with_context(skip_pending_sync=True).write({"name": new_name})
        # Archivado bidireccional
        if "active" in vals and not self.env.context.get("skip_project_archive_sync"):
            for project in self:
                if project.pending_inbox_id:
                    project.pending_inbox_id.with_context(skip_pending_archive_sync=True).write({"active": vals.get("active")})
        return res


