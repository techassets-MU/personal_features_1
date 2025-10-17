from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectPendingInbox(models.Model):
    _name = "project.pending.inbox"
    _description = "Pendientes indefinidos para clasificar como tarea o proyecto"
    _order = "create_date desc"

    sequence = fields.Integer(string='Secuencia', default=10)
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
    active = fields.Boolean(string="Activo", default=True)

    # Trazabilidad inversa
    task_id = fields.Many2one("project.task", string="Tarea creada", readonly=True)
    project_id = fields.Many2one("project.project", string="Proyecto creado", readonly=True)

    # Campos auxiliares obligatorios al convertir
    task_deadline = fields.Date(
        string="Fecha límite (tarea)",
        help="Si es Urgente o Urgente e Importante, la tarea requiere una fecha límite.",
    )
    project_company_id = fields.Many2one(
        "res.company", 
        string="Compañía del proyecto",
        default=lambda self: self.env.company,  # Compañía actual del usuario
        help="Compañía a la que pertenecerá el proyecto."
    )


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
        # Asegurar que siempre haya una compañía
        if self.project_company_id:
            vals["company_id"] = self.project_company_id.id
        else:
            # Usar la compañía del usuario actual como fallback
            vals["company_id"] = self.env.company.id

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
        # Bloquear cambio de tipo si ya existe tarea o proyecto creado
        if "type" in vals:
            for record in self:
                if record.task_id or record.project_id:
                    raise ValidationError(
                        _(
                            "No puede cambiar el tipo porque ya se generó una Tarea o Proyecto desde este registro. Archive este pendiente y cree uno nuevo con el tipo correcto."
                        )
                    )
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
        # Sincronizar archivado (active) bidireccional cuando cambia en pending
        if "active" in vals and not self.env.context.get("skip_pending_archive_sync"):
            new_active = vals.get("active")
            for record in self:
                if record.task_id:
                    record.task_id.with_context(skip_task_archive_sync=True).write({"active": new_active})
                if record.project_id:
                    record.project_id.with_context(skip_project_archive_sync=True).write({"active": new_active})
        return res


    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribir create para crear automáticamente tarea o proyecto"""
        records = super().create(vals_list)
        
        # Crear tarea o proyecto automáticamente según el tipo
        for record in records:
            if record.type == "task" and not record.task_id:
                try:
                    record._create_task_from_pending()
                except Exception as e:
                    _logger.error(f"Error creando tarea en create: {e}", exc_info=True)
                    
            elif record.type == "project" and not record.project_id:
                try:
                    record._create_project_from_pending()
                except Exception as e:
                    _logger.error(f"Error creando proyecto en create: {e}", exc_info=True)
        
        return records