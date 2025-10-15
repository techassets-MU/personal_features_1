from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectPendingInbox(models.Model):
    _name = "project.pending.inbox"
    _description = "Pendientes indefinidos para clasificar como tarea o proyecto"
    _order = "create_date desc"

    name = fields.Char(string="Nombre", required=True)
    type = fields.Selection(
        selection=[("task", "Tarea"), ("project", "Proyecto")],
        string="Tipo",
        help="Seleccione si este pendiente debe convertirse en Tarea o Proyecto.",
    )
    priority_quadrant = fields.Selection(
        selection=[
            ("do", "Urgente e Importante (Hacer)"),
            ("delegate", "Urgente (Delegar)"),
            ("plan", "Importante (Planificar)"),
            ("archive", "No Urgente y No Importante (Eliminar/Archivar)"),
        ],
        string="Cuadrante de prioridad",
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Usuario",
        default=lambda self: self.env.user,
        help="Usuario que creó el pendiente.",
    )
    done = fields.Boolean(string="Hecho")

    # Trazabilidad inversa
    task_id = fields.Many2one("project.task", string="Tarea creada", readonly=True)
    project_id = fields.Many2one("project.project", string="Proyecto creado", readonly=True)

    # Campos auxiliares obligatorios al convertir
    task_deadline = fields.Date(
        string="Fecha límite (tarea)",
        help="Si es Urgente o Urgente e Importante, la tarea requiere una fecha límite.",
    )
    project_company_id = fields.Many2one("res.company", string="Compañía del proyecto")

    @api.constrains("priority_quadrant", "type", "task_deadline")
    def _check_deadline_when_urgent(self):
        for record in self:
            is_urgent = record.priority_quadrant in ("do", "delegate")
            if is_urgent and record.type == "task":
                if not record.task_deadline:
                    raise ValidationError(
                        _(
                            "Para pendientes Urgentes o Urgentes e Importantes convertidos en Tarea, es obligatorio definir una fecha límite."
                        )
                    )

    @api.onchange("type")
    def _onchange_type_note(self):
        if self.type == "project":
            # No acciones obligatorias adicionales por requerimiento
            pass

    def _create_task_from_pending(self):
        self.ensure_one()
        # Buscar proyecto por defecto (Inbox) por XML-ID; fallback: primero disponible; último recurso: crearlo
        project = self.env.ref(
            "project_pending_inbox.project_pending_inbox_default_project",
            raise_if_not_found=False,
        )
        if not project:
            project = self.env["project.project"].search([], limit=1)
        if not project:
            project = self.env["project.project"].create({"name": "Inbox"})
        vals = {
            "name": self.name,
            "pending_inbox_id": self.id,
            "user_ids": [(4, self.user_id.id)] if self.user_id else False,
        }
        if self.task_deadline:
            vals["date_deadline"] = self.task_deadline
        task = self.env["project.task"].create(vals | {"project_id": project.id} if project else vals)
        self.task_id = task.id
        return task

    def action_convert_to_task(self):
        self.ensure_one()
        if self.task_id:
            return self._action_open_task()
        self._create_task_from_pending()
        return self._action_open_task()

    def _create_project_from_pending(self):
        self.ensure_one()
        vals = {
            "name": self.name,
            "pending_inbox_id": self.id,
        }
        if self.project_company_id:
            vals["company_id"] = self.project_company_id.id
        project = self.env["project.project"].create(vals)
        self.project_id = project.id
        return project

    def action_convert_to_project(self):
        self.ensure_one()
        if self.project_id:
            return self._action_open_project()
        self._create_project_from_pending()
        return self._action_open_project()

    def _action_open_task(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "res_id": self.task_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def _action_open_project(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "res_id": self.project_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.onchange("type")
    def _onchange_type_auto_create(self):
        # Se crea cuando el usuario decide explícitamente mediante botones; no automático en onchange
        pass

    def write(self, vals):
        new_name = vals.get("name")
        res = super().write(vals)
        # Auto crear según tipo seleccionado si aún no existe
        for record in self:
            if vals.get("type") == "task" and not record.task_id:
                record._create_task_from_pending()
            elif vals.get("type") == "project" and not record.project_id:
                record._create_project_from_pending()
        # Propagar cambio de nombre a tarea/proyecto vinculados (evitar bucles con contexto)
        if new_name and not self.env.context.get("skip_pending_sync"):
            for record in self:
                if record.task_id:
                    record.task_id.with_context(skip_task_sync=True).write({"name": new_name})
                if record.project_id:
                    record.project_id.with_context(skip_project_sync=True).write({"name": new_name})
        return res


