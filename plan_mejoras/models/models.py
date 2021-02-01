from pip._vendor.six import print_

from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError


class Tarea(models.Model):
    _name = "pm.tarea"
    _description = "Tareas"
    _inherit = "mail.thread"

    name = fields.Char(string="Tarea", required=True)
    description = fields.Html(string="Descripción", default="""<p>Tarea creada por: Administrador</p>""",
                              track_visibility="onchange")
    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    expirado = fields.Selection(selection=[("no_expired", "No Expirado"), ("expired", "Expirado")],
                               string="Tiempo Límite",
                               default="no_expired")

    ponderacion = fields.Selection(
        selection=[("nulo", "Sin Calificar"), ("noc", "No Cumple"), ("cep", "Cumple en parte"), ("cum", "Cumple")],
        string="Ponderación", default="nulo", required=True)

    estado = fields.Boolean(default=False)

    estado_id = fields.Many2one("pm.estado", string="Estado", ondelete='restrict', required=True,
                                   default=lambda self: self.env['pm.estado'].search([], limit=1),
                                   group_expand='_group_expand_stage_ids', track_visibility="onchange")

    user_id = fields.Many2one("res.users", string="Docente", required=True, default=lambda self: self.env.uid)

    plan_id = fields.Many2one("pm.plan", string="Plan Mejoras")

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
            # sum(record.mapped("porcentaje_ponderacion"))


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


    
    #Sobrecarga de Create
    '''
    @api.model
    def create(self, vals):
        name = vals.get("name","-")
        amount = vals.get("amount","0")
        type_mov = vals.get("type_mov","")
        date = vals.get("date", "")

        #para la cantidad de movimientos del usuario
        user = self.env.user
        count_movs = user.count_mov
        #Condicion para controlar los 5 movimientos de usuarios Free
        if count_movs >= 5 and user.has_group("saldo_app.res_groups_user_free"):
            raise ValidationError("Tu cuenta permite creacion de 5 movimientos")

        notas = """<p>Tipo de Movimiento: {}</p><p>Nombre: {}</p><p>Monto: {}</p><p>Fecha: {}<br></p>"""
        vals["notas"] = notas.format(type_mov, name, amount, date)
        return super(Movimiento, self).create(vals)
    '''


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

    @api.depends("groups_id", "is_group_admin")
    def _compute_is_group_admin(self):
        self.is_group_admin = self._origin.has_group('plan_mejoras.res_groups_administrador')
     
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

    tarea_ids = fields.One2many("pm.tarea", "plan_id")

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
                    print(docente.name)
                    print(docente.is_group_admin)
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

        return {
            "type": "ir.actions.client",
            "tag": "mail.discuss",
            "target": "main"
        }