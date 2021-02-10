import datetime
from _ast import expr

from docutils.nodes import section

from addons.website.models.res_users import ResUsers
from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError


class Tarea(models.Model):
    _name = "pm.tarea"
    _description = "Tareas"
    _inherit = "mail.thread"

    name = fields.Char(string="Tarea", required=True)
    description = fields.Html(string="Descripción", default="Tarea creada por: Administrador",
                              track_visibility="onchange")
    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True)

    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    expirado = fields.Selection(selection=[("no_expired", "No Expirado"), ("expired", "Expirado")],
                               string="Tiempo Límite",
                               default="no_expired")

    ponderacion = fields.Selection(
        selection=[("nulo", "Sin Calificar"), ("noc", "No Cumple"), ("cep", "Cumple en parte"), ("cum", "Cumple")],
        string="Ponderación", default="nulo")

    estado = fields.Boolean(default=False)

    estado_id = fields.Many2one("pm.estado", string="Estado", ondelete='restrict', required=True,
                                   default=lambda self: self.env['pm.estado'].search([], limit=1),
                                   group_expand='_group_expand_stage_ids', track_visibility="onchange")

    user_id = fields.Many2one("res.users", string="Docente", required=True, default=lambda self: self.env.uid)

    plan_id = fields.Many2one("pm.plan", string="Plan Mejoras", ondelete="cascade")

    debilidad_id = fields.Many2one("pm.debilidad", string="Debilidades")

    email = fields.Char(related="user_id.email", string="Correo Electronico")

    evicencia_id = fields.One2many("pm.evidencia", "tareas_ids")

    etiqueta_ids = fields.Many2many(
        'pm.etiqueta', 'pm_etiqueta_rel',
        'etiqueta_id', 'tarea_id', string='Etiquetas')

    @api.model
    def _group_expand_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def check_expiry(self):
        today = fields.Date.today()
        lista_tareas = self.env["pm.tarea"].search([])
        for tarea in lista_tareas:
            if tarea.expirado == "no_expired" and tarea.fecha_fin < today:
                tarea.expirado = "expired"
                if (tarea.user_id.has_group('plan_mejoras.res_groups_docente')):
                    template_rec = self.env.ref('plan_mejoras.email_template_tarea_expirada')
                    template_rec.write({'email_to': tarea.user_id.email})
                    template_rec.send_mail(tarea.id, force_send=True)

    def send_notification_tarea(self):
        error = False
        today = fields.Date.today()
        tareas = self.env["pm.tarea"].search([])
        for tarea in tareas:
            aux7 = tarea.fecha_fin - datetime.timedelta(days=7)
            aux3 = tarea.fecha_fin - datetime.timedelta(days=3)
            if (tarea.user_id.has_group('plan_mejoras.res_groups_docente')):
                if aux7 == today or aux3 == today:
                    try:
                        template_rec = self.env.ref('plan_mejoras.email_template_tarea')
                        template_rec.write({'email_to': tarea.user_id.email})
                        template_rec.send_mail(tarea.id, force_send=True)
                    except:
                        error = True
        if error==True:
            self.env.user.notify_danger(message='Se produjo un error al enviar la Notificación al correo electrónico')

    @api.onchange('ponderacion')
    def send_notification_tarea_ponderada(self):
        error = False
        if self.ponderacion != 'nulo':
            aux = self.ponderacion
            try:
                template_rec = self.env.ref('plan_mejoras.email_template_tarea_ponderada')
                template_rec.write({'email_to': self.user_id.email})
                template_rec.send_mail(self._origin.id, force_send=True)
                self.ponderacion = aux
                self.estado = True
            except:
                error = True
            if error==True:
                self.env.user.notify_danger(
                    message='Se produjo un error al enviar la Notificación al correo electrónico')


class Estado(models.Model):
    _name = "pm.estado"
    _description = "Estado"
    _order = 'sequence'

    name = fields.Char(string="Nombre", required=True)
    description = fields.Char(string="Descripción")
    sequence = fields.Integer()


class Evidencia(models.Model):
    _name = "pm.evidencia"
    _description = "Evidencias"

    name = fields.Char(string='Nombre', required=True, translate=True)
    evidencia = fields.Html(string="Evidencias")

    tareas_ids = fields.Many2one("pm.tarea", string="Tareas", ondelete='cascade')

    _sql_constraints = [
        ('name_unique', 'unique (name)', "El nombre de la Evidencia ya existe!"),
    ]


class Etiqueta(models.Model):
    _name = "pm.etiqueta"
    _description = "Etiqueta"

    name = fields.Char(string='Nombre',required=True, translate=True)
    description = fields.Char(string='Descripción', translate=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_unique', 'unique(name)', "El nombre de la Etiqueta ya existe!"),
    ]

class CriterioNombre(models.Model):
    _name = "pm.criterionombre"
    _description = "Nombre del Criterio"

    name = fields.Char(string="Criterio de Evaluación", required=True)
    description = fields.Char(string="Descripción")
    porcentaje_ponderacion = fields.Integer(string="% Ponderación", required=True)
    total_val = fields.Float("Total Valoracion", compute="_compute_valoracion_porcentaje", store=True)

    criterios_ids = fields.One2many("pm.criterio", "criterionombre_id")

    _sql_constraints = [
        ('name_unique', 'unique(name)', "El nombre del Criterio ya existe!"),
    ]

    @api.constrains('porcentaje_ponderacion')
    def _check_porcentaje_ponderacion(self):
        for record in self:
            if record.porcentaje_ponderacion < 1:
                raise ValidationError("El porcentaje de Ponderación debe ser mayor a 0.")

    @api.depends("porcentaje_ponderacion")
    def _compute_valoracion_porcentaje(self):
        criterio = self.env["pm.criterionombre"].search([])
        total = 0
        for record in criterio:
            total = total + record.porcentaje_ponderacion
        self.total_val = total
        if self.total_val > 100:
            raise ValidationError(
                "La Suma de las ponderaciones No debe superar el 100%")


class Criterio(models.Model):
    _name = "pm.criterio"
    _description = "Nota del Criterio Evaluación"

    calificacion = fields.Float(string="Calificación", required=True)

    criterionombre_id = fields.Many2one("pm.criterionombre", string="Nombre del Criterio", ondelete='restrict',
                                        required=True,
                                        default=lambda self: self.env['pm.criterionombre'].search([], limit=1),
                                        group_expand='_group_expand_stage_ids', track_visibility="onchange")

    user_id = fields.Many2one("res.users", string="Docente", required=True, default=lambda self: self.env.uid)


    @api.onchange('calificacion', 'criterionombre_id')
    def _check_calificacion(self):
        porcentaje = 0
        criterio = self.env["pm.criterionombre"].search([])
        for c in criterio:
            if self.criterionombre_id.id == c.id:
                porcentaje = c.porcentaje_ponderacion

        if self.calificacion < 0:
            raise ValidationError("Calificación no puede ser Negativa")
        else:
            if self.calificacion > porcentaje:
                raise ValidationError("Calificación supera rango de Valoración")


class ResUser(models.Model):
    _inherit = "res.users"

    us_cat = fields.Selection(
        selection=[("insatisfactorio", "Insatisfactorio"), ("poco_satisfactorio", "Poco Satisfactorio")
            , ("satisfactorio", "Satisfactorio"), ("destacado", "Destacado")],
        string="Valoracion Cuantitativa", store=True, compute="_compute_valoracion_docente")

    count_tarea = fields.Integer(string="Tareas por Ponderar", compute="_contador_tareas", store=True)

    is_group_admin = fields.Boolean(
        string='Es Administrador',
        compute="_compute_is_group_admin",
        store=True
    )

    tarea_ids = fields.One2many("pm.tarea", "user_id")

    criterio_ids = fields.One2many("pm.criterio", "user_id")

    total_val = fields.Float("Total Valoracion", compute="_compute_valoracion_docente", store=True)

    plan_id = fields.One2many("pm.plan", "user_ids")


    def get_groups_usesr_email(self):
        emails = []
        usuarios = self.env["res.users"].search([])
        for usuario in usuarios:
            if (usuario.has_group('plan_mejoras.res_groups_docente')):
                emails.append(usuario.email)

        return emails

    def action_send_email(self):
        all_eamils = self.get_groups_usesr_email()

        for email in all_eamils:
            template_rec = self.env.ref('plan_mejoras.email_template_inicializarPM')
            template_rec.write({'email_to': email})

            template_rec.send_mail(self.id, force_send=True)


    @api.depends("groups_id", "is_group_admin")
    def _compute_is_group_admin(self):
        for record in self:
            record.is_group_admin = record._origin.has_group('plan_mejoras.res_groups_administrador')
     
    @api.depends("tarea_ids.ponderacion")
    def _contador_tareas(self):
        lista_plan = self.env["pm.plan"].search([])
        for plan in lista_plan:
            if plan.finalizado == False:
                for record in self:
                    movs = record.tarea_ids.filtered(
                        lambda r: r.ponderacion == 'nulo')
                    record.count_tarea = len(movs)

    @api.depends('total_val', 'criterio_ids', 'us_cat')
    def _compute_valoracion_docente(self):
        nota = self.env["pm.criterio"].search([])
        #criterios = self.env["pm.criterionombre"].search([])
        total = 0
        us_cat = ""
        for record in nota:
            if record.user_id.id == self._origin.id:
                total = total + record.calificacion
        if total >= 0 and total <= 40:
            us_cat = "insatisfactorio"
        elif total > 40 and total <= 60:
            us_cat = "poco_satisfactorio"
        elif total > 60 and total <= 80:
            us_cat = "satisfactorio"
        elif total > 80 and total <= 100:
            us_cat = "destacado"
        else:
            raise ValidationError("El valor esta fuera de rango (0-100)")

        self.us_cat = us_cat
        self.total_val = total

    def vista_tree(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Plan Actividades",
            "res_model": "pm.plan",
            "docente": self.id,
            "views": [(False, "kanban")],
            "target": "self",
            "context": {"id_def": self.id}
        }


class Plan(models.Model):
    _name = "pm.plan"
    _description = "Plan Mejoras"

    name = fields.Char(required=True, translate=True, string="Nombre")
    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    objetivo = fields.Html(string="Objetivos")
    introduccion = fields.Html(string="Introducción")
    conclusion = fields.Html(string="Conclusión")
    recomendacion = fields.Html(string="Recomendación")

    add_resultados = fields.Boolean(default=True, string="Agregar resultados de la EDD")

    add_anexos = fields.Boolean(default=True, string="Incluir Anexos")

    estado_Inicializar = fields.Boolean(default=True)

    estado_Comunicar = fields.Boolean(default=False)

    finalizado = fields.Boolean(default=False)

    tarea_ids = fields.One2many("pm.tarea", "plan_id",  ondelete="cascade")

    user_ids = fields.Many2one("res.users", string="Docente")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El Plan Mejoras ya existe!"),
    ]

    def inicializar(self):
        return {
            'name': 'Inicializar Plan Mejoras',
            'type': 'ir.actions.act_window',
            'res_model': 'pm.confirm_iniciar',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            "context": {"id_ini": self.id}
        }
        # raise Warning('Las actividades se mostraran a los docentes y se enviará una '
        #             'notificación de la inicialización del Plan Mejoras.')

    def comunicar(self):
        return {
            'name': 'Comunicar Plan Mejoras',
            'type': 'ir.actions.act_window',
            'res_model': 'pm.confirm_wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            "context": {"id_infor": self.id}
        }

    def vista_tree_tareas(self):
        id_def = self.env.context.get('id_def')
        return {
            "type": "ir.actions.act_window",
            "name": "Tareas",
            "res_model": "pm.tarea",
            "views": [(False, "kanban"), (False, "form"), (False, "tree")],
            "target": "self",
            "domain": [["plan_id", "=", self.id], ["user_id", "=", id_def]]
        }

    def send_notification_tarea_consejo(self):
        emails = []
        today = fields.Date.today()
        planes = self.env["pm.plan"].search([])
        for plan in planes:
            if plan.finalizado == False:
                fecha_inicio = plan.fecha_inicio
                fecha_fin = plan.fecha_fin
                dias = abs(fecha_inicio - fecha_fin).days
                aux50 = plan.fecha_fin - datetime.timedelta(days=dias / 2)
                aux75 = plan.fecha_fin - datetime.timedelta(days=dias / 3)
                for docente in plan.user_ids:
                    if (docente.has_group('plan_mejoras.res_groups_docente_consejo')):
                        if aux50 == today:
                            template_rec = self.env.ref('plan_mejoras.control_tareas_consejo50')
                            template_rec.write({'email_to': docente.email})
                            template_rec.send_mail(plan.id, force_send=True)
                        elif aux75 == today:
                            template_rec = self.env.ref('plan_mejoras.control_tareas_consejo75')
                            template_rec.write({'email_to': docente.email})
                            template_rec.send_mail(plan.id, force_send=True)



class Debilidad(models.Model):
    _name = "pm.debilidad"
    _description = "Debilidades"

    name = fields.Char(required=True, translate=True, string="Nombre")
    description = fields.Char(string="Descripción")

    tarea_ids = fields.One2many("pm.tarea", "debilidad_id")


class confirm_wizard(models.TransientModel):
    _name = 'pm.confirm_wizard'

    yes_no = fields.Char(default='Está seguro que desea comunicar el Plan Mejoras? \n Recuerde que debe socializarlo.')

    def yes(self):
        id_def = self.env.context.get('id_infor')
        self.env["pm.plan"].browse(id_def).write({"estado_Inicializar": False})
        self.env["pm.plan"].browse(id_def).write({"estado_Comunicar": True})
        self.env.cr.commit()
        return {
            "type": "ir.actions.client",
            "tag": "mail.discuss",
            "target": "main"
        }


class confirm_wizardI(models.TransientModel):
    _name = 'pm.confirm_iniciar'

    yes_no = fields.Char(
        default='Las actividades se mostraran a los docentes y se enviará una notificación de la inicialización del Plan Mejoras.')

    def yes(self):
        info_id = self.env.context.get('id_ini')
        lista_tareas = self.env["pm.tarea"].search([])
        lista_docentes = self.env["res.users"].search([])
        for tarea in lista_tareas:
            for docente in lista_docentes:
                if int(info_id) == int(tarea.plan_id):
                    if docente.is_group_admin == False:
                        self.env["pm.tarea"].create({"name": tarea.name,
                                                     "description": tarea.description,
                                                     "fecha_inicio": tarea.fecha_inicio,
                                                     "fecha_fin": tarea.fecha_fin,
                                                     "ponderacion": tarea.ponderacion,
                                                     "estado_id": '1',
                                                     "user_id": docente.id,
                                                     "plan_id": info_id,
                                                     "debilidad_id": tarea.debilidad_id.id,
                                                     "etiqueta_ids": tarea.etiqueta_ids})

        self.env["pm.plan"].browse(info_id).write({"estado_Inicializar": True})
        self.env.cr.commit()
        lista_planes = self.env["pm.tarea"].search([])
        lista_docentes = self.env["res.users"].search([])
        for plan in lista_planes:
            if plan.id == info_id:
                for docente in lista_docentes:
                    self.env["pm.plan"].browse(info_id).write({"user_ids": docente.id})

        ResUser.action_send_email(self.env.user)
        return {
            "type": "ir.actions.client",
            "tag": "mail.discuss",
            "target": "main"
        }