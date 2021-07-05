from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError
import datetime


class Tarea(models.Model):
    _name = "pm.tarea"
    _description = "Tareas"
    _inherit = "mail.thread"

    name = fields.Char(string="Nombre de la Tarea", required=True)
    description = fields.Html(string="Descripción de la Tarea",
                              default="Tarea creada del Plan Mejoras de la "
                                      "Evaluación al Desempeño Docente",
                              track_visibility="onchange")
    fecha_inicio = fields.Date(string="Fecha de Inicio",
                               required=True)
    fecha_fin = fields.Date(string="Fecha Fin",
                            required=True)
    expirado = fields.Selection(selection=[("no_expired", "No Expirado"), ("expired", "Expirado")],
                               string="Tiempo Límite",
                               default="no_expired")
    ponderacion = fields.Selection(
        selection=[("nulo", "Sin Calificar"), ("noc", "No Cumple"),
                   ("cep", "Cumple en parte"), ("cum", "Cumple")],
        string="Ponderación", default="nulo")
    estado = fields.Boolean(default=False)
    tiene_evidencia = fields.Boolean(default=False, string="Posee Evidencia")

    estado_id = fields.Many2one("pm.estado", string="Estado", ondelete='restrict', required=True,
                                   default=lambda self: self.env['pm.estado'].search([], limit=1),
                                   group_expand='_group_expand_stage_ids', track_visibility="onchange")

    user_id = fields.Many2one("res.users", string="Docente", required=True, ondelete="cascade", default=lambda self: self.env.uid)

    plan_id = fields.Many2one("pm.plan", string="Plan Mejoras", ondelete="cascade")

    debilidad_id = fields.Many2one("pm.debilidad", string="Debilidades")

    email = fields.Char(related="user_id.email", string="Correo Electronico")

    evicencia_id = fields.One2many("pm.evidencia", "tareas_ids")

    etiqueta_ids = fields.Many2many(
        'pm.etiqueta', 'pm_etiqueta_rel',
        'etiqueta_id', 'tarea_id', string='Etiquetas')

    @api.constrains('fecha_inicio')
    def _validar_fecha_tarea(self):
        '''
            Verificar que las fecha inicio y fin de la clase Tareas cumplan el siguiente control:
            La fecha fin de la Tarea sea mayor que la fecha inicio.
            La fecha fin de la Tarea sea mayor a la fecha actual.
        '''

        today = fields.Date.today()
        for record in self:
            if record.plan_id.finalizado == False:
                fecha_ini_tarea = record.fecha_inicio
                fecha_fin_tarea = record.fecha_fin
                fecha_fin_plan = record.plan_id.fecha_fin
                fecha_ini = datetime.datetime.strptime(str(fecha_ini_tarea), "%Y-%m-%d")
                fecha_fin = datetime.datetime.strptime(str(fecha_fin_tarea), "%Y-%m-%d")
                fecha_plan = datetime.datetime.strptime(str(fecha_fin_plan), "%Y-%m-%d")
                if fecha_plan.date() > fecha_fin.date():
                    if fecha_fin.date() < today or fecha_ini.date() > fecha_fin.date():
                        raise ValidationError(("Verifique las Fechas ingresadas para la tarea: %s") % record.name)
                else:
                    raise ValidationError(("La Fecha de Finalización ingresadas para la tarea: %s No Puede ser mayor a la de Finalización del Plan Mejoras de la EDD") % record.name)

    @api.constrains('fecha_fin')
    def fecha_fin_modificada(self):
        """
            Verificar si la fecha fin de una Tarea es mayor al día actual, cambiar estado de la Tarea a True(Finalizada)
            y el atributo expirado a 'expired(Expirado)'
        """

        today = fields.Date.today()
        for record in self:
            if record.fecha_fin < today:
                record.estado = True
                record.expirado = "expired"
            elif today < record.fecha_fin:
                record.estado = False
                record.expirado = "no_expired"

    @api.model
    def _group_expand_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def check_expiry(self):
        """
            Método ejecutado con acción planificada 'cron', para notificar mediante correo electrónico a los
            usuarios sobre la expiración de una Tarea en específico y cambio del estado de la tarea.
        """

        today = fields.Date.today()
        lista_tareas = self.env["pm.tarea"].search([])
        for tarea in lista_tareas:
            if tarea.expirado == "no_expired" and tarea.fecha_fin < today:
                tarea.expirado = "expired"
                tarea.estado = True
                if (tarea.user_id.has_group('plan_mejoras.res_groups_docente')) and tarea.ponderacion == 'nulo':
                    template_rec = self.env.ref('plan_mejoras.email_template_tarea_expirada')
                    template_rec.write({'email_to': tarea.user_id.email})
                    template_rec.send_mail(tarea.id, force_send=True)
            elif tarea.expirado == "expired" and today < tarea.fecha_fin:
                tarea.expirado = "no_expired"
                tarea.estado = False

    def send_notification_tarea(self):
        """
            Método ejecutado con acción planificada 'cron', para poder controlar el cumplimiento de una Tarea, mediante
            el envío de una notificación mediante correo electrónico en tiempos dinamicos, determinados
            por el administrador.
        """

        error = False
        today = fields.Date.today()
        tareas = self.env["pm.tarea"].search([])
        notificacion = self.env["pm.notificaciond"].search([])
        for tarea in tareas:
            if (tarea.user_id.has_group('plan_mejoras.res_groups_docente')):
                for noti in notificacion:
                    dia = noti.dias_notificacion
                    aux = tarea.fecha_fin - datetime.timedelta(days=dia)
                    if aux == today:
                        try:
                            template_rec = self.env.ref('plan_mejoras.email_template_tarea')
                            template_rec.write({'email_to': tarea.user_id.email})
                            template_rec.send_mail(tarea.id, force_send=True)
                        except:
                            error = True
        if error==True:
            self.env.user.notify_danger(message='Se produjo un error al enviar la Notificación al correo electrónico')


    @api.constrains('ponderacion')
    def send_notification_tarea_ponderada(self):
        """
            Método ejecutado con acción planificada 'cron', para notificar mediante correo electrónico
            que una tarea en específico ha sido calificada..
        """

        for record in self:
            error = False
            if record.ponderacion != 'nulo':
                record.estado = True
                try:
                    template_rec = record.env.ref('plan_mejoras.email_template_tarea_ponderada')
                    template_rec.write({'email_to': record.user_id.email})
                    template_rec.send_mail(record._origin.id, force_send=True)
                except:
                    error = True
                if error==True:
                    record.check_expiryenv.user.notify_danger(
                        message='Se produjo un error al enviar la Notificación al correo electrónico')

    @api.constrains("evicencia_id")
    def _contador_evidencia(self):
        for record in self:
            aux = False
            movs = record.evicencia_id.filtered(
                lambda r: record.plan_id.finalizado == False)
            if len(movs) > 0:
                aux = True
            record.tiene_evidencia = aux


class Estado(models.Model):
    _name = "pm.estado"
    _description = "Estado"
    _order = 'sequence'

    name = fields.Char(string="Nombre", required=True)
    description = fields.Char(string="Descripción")
    sequence = fields.Integer()

    _sql_constraints = [
        ('name_unique', 'unique (name)',
         "El nombre del Estado ya existe!"),
    ]

class Evidencia(models.Model):
    _name = "pm.evidencia"
    _description = "Evidencias"

    name = fields.Char(string='Nombre',
                       required=True,
                       translate=True)
    evidencia = fields.Html(string="Evidencias")

    tareas_ids = fields.Many2one("pm.tarea",
                                 string="Tareas",
                                 ondelete='cascade')



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

    criterios_ids = fields.One2many("pm.criterio", "criterionombre_id", ondelete="cascade")

    _sql_constraints = [
        ('name_unique', 'unique(name)', "El nombre del Criterio ya existe!"),
    ]

    @api.constrains('porcentaje_ponderacion')
    def _check_porcentaje_ponderacion(self):
        """
            Controlar que la variable porcentaje_ponderacion, sea mayor a 0
        """

        for record in self:
            if record.porcentaje_ponderacion < 1:
                raise ValidationError("El porcentaje de Ponderación debe ser mayor a 0.")

    @api.depends("porcentaje_ponderacion")
    def _compute_valoracion_porcentaje(self):
        """
            Controlar que la suma de poderaciones no supere el 100%
        """

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

    criterionombre_id = fields.Many2one("pm.criterionombre", string="Nombre del Criterio",
                                        required=True,
                                        default=lambda self: self.env['pm.criterionombre'].search([], limit=1),
                                        group_expand='_group_expand_stage_ids', track_visibility="onchange", ondelete="cascade")

    user_id = fields.Many2one("res.users", string="Docente", required=True, default=lambda self: self.env.uid)


    @api.onchange('calificacion', 'criterionombre_id')
    def _check_calificacion(self):
        """
            Controlar que la calificacion de un criterio de evaluacion no sea negativo y,
            validar que no supere el porcentaje de ponderacion detinado a ese criterio de
            evaluacion.
        """

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
        string="Valoracion Cualitativa", store=True, compute="_compute_valoracion_docente")

    count_tarea = fields.Integer(string="Tareas por Ponderar", compute="_contador_tareas", store=True)

    is_group_admin = fields.Boolean(
        string='Es Administrador',
        compute="_compute_is_group_admin",
        store=True
    )

    tarea_ids = fields.One2many("pm.tarea", "user_id", ondelete="cascade")

    criterio_ids = fields.One2many("pm.criterio", "user_id")

    total_val = fields.Float("Total Valoracion", compute="_compute_valoracion_docente", store=True)

    plan_id = fields.Many2one("pm.plan", string="Plan Mejoras")



    def get_groups_usesr_email(self):
        """
            Obtener los emails de los usuarios pertenecientes al grupo docentes(res_groups_docente).
            :return: Una lista con los emails de los docentes.
        """

        emails = []
        usuarios = self.env["res.users"].search([])
        for usuario in usuarios:
            if (usuario.has_group('plan_mejoras.res_groups_docente')):
                emails.append(usuario.email)
        return emails

    def action_send_email(self):
        """
            Notificar mediante correo electrónico el inicio del Plan Mejoras de la Evaluación al
            Desempeño Docente, solo para el grupo deocente.
        """

        usuarios = self.env["res.users"].search([])
        error = False
        try:
            for usuario in usuarios:
                if (usuario.has_group('plan_mejoras.res_groups_docente')):
                    template_rec = usuario.env.ref('plan_mejoras.email_template_inicializarPM')
                    template_rec.write({'email_to': usuario.email})
                    template_rec.send_mail(usuario.id, force_send=True)
        except:
            error = True
        if error==True:
            self.env.user.notify_danger(message='Se produjo un error al enviar la Notificación al correo electrónico')


    @api.depends("groups_id", "is_group_admin")
    def _compute_is_group_admin(self):
        """
            Calcular si un usuario pertenece al grupo Administrador.
        """

        for record in self:
            record.is_group_admin = record._origin.has_group('plan_mejoras.res_groups_administrador')
     
    @api.depends("tarea_ids.ponderacion")
    def _contador_tareas(self):
        """
            Calcular el número de Tareas por usuario pendientes a calificar o que se encuentran
            sin asignar alguna ponderación.
        """
        for record in self:
            movs = record.tarea_ids.filtered(
                lambda r: r.ponderacion == 'nulo' and r.plan_id.finalizado == False)
            record.count_tarea = len(movs)

    @api.depends('total_val', 'criterio_ids', 'us_cat')
    def _compute_valoracion_docente(self):
        """
            Calcular la valoración cualitativa, respecto a la suma de los criterio de calificación.
            Asignación de la suma a la variable total_val.
        """

        nota = self.env["pm.criterio"].search([])
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
        """
            Redireccionar desde vista Docentes al Plan de Mejoras, mostrando el
            Plan de Actividades según el estado.
            :returns: Acción de ventana que contiene la vista Kanban del
            Plan de Actividades.
        """

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
    _description = "Plan Mejoras de la Evaluación al Desempeño Docente"

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

    user_ids = fields.One2many("res.users", "plan_id")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El Plan Mejoras ya existe!"),
    ]


    @api.model
    def create(self, vals):
        """
            Sobrecarga del método create del Plan Mejoras para controlar la
            creación de un solo registro activo vigente, además de validar que
            la fecha de finalización del Plan sea mayor a la fecha actual y la
            fecha inicio del Plan menor a la fecha de finalización.
            :param vals: Campos del modelo, como una lista de diccionarios.
            :returns: La creación de un nuevo Plan.
        """
        registros = self.env["pm.plan"].search([])
        aux = vals.get('fecha_inicio')
        aux1 = vals.get('fecha_fin')
        fecha_ini = datetime.datetime.strptime(str(aux), "%Y-%m-%d")
        fecha_fin = datetime.datetime.strptime(str(aux1), "%Y-%m-%d")
        today = fields.Date.today()
        if fecha_fin.date() > today and fecha_ini.date() < fecha_fin.date():
            for record in registros:
                if record.finalizado == False:
                    raise ValidationError(
                        "Ya existe un Plan Mejoras vigente en este Periodo!")
                    break
        else:
            raise ValidationError(
                "Verifique las Fechas ingresadas para el Plan Mejoras!")
        return super(Plan, self).create(vals)

    @api.constrains('fecha_fin')
    def fecha_fin_modificada(self):
        """
            Controlar estado finalizado del Plan, dependiendo de que la fecha fin mayor a fecha actual o
            viceversa.
        """

        today = fields.Date.today()
        if self.fecha_fin < today:
            self.finalizado = True
        elif today < self.fecha_fin:
            self.finalizado = False


    def inicializar(self):
        """
            Mostrar un cuadro de dialogo para la confirmación del Inicio del Plan Mejoras.
            :returns: Acción de ventana que contiene el cuadro de dialogo.
        """

        return {
            'name': 'Inicializar Plan Mejoras',
            'type': 'ir.actions.act_window',
            'res_model': 'pm.confirm_iniciar',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            "context": {"id_ini": self.id}
        }

    def comunicar(self):
        """
            Mostrar un cuadro de dialogo para la confirmación de la comunicación del Plan Mejoras.
            :returns: Acción de ventana que contiene el cuadro de dialogo.
        """

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
        """
            Redireccionar desde vista Kanban de Plan de Actividades a Tareas.
            :returns: Acción de ventana que contiene las vistas Kanban, form y tree de la clase Tarea.
        """

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
        """
            Notificacion mediante correo electronico a los usuarios del grupo Consejo Consultivo
            (res_group_docenrte_consejo), solicitando la revision del Plan Mejoras de cada uno de los docentes integrantes.
        """

        emails = []
        error = False
        today = fields.Date.today()
        planes = self.env["pm.plan"].search([])
        for plan in planes:
            if plan.finalizado == False:
                registro = self.env["pm.notificacionc"].search([])
                fecha_inicio = plan.fecha_inicio
                fecha_fin = plan.fecha_fin
                dias = abs(fecha_inicio - fecha_fin).days
                if len(registro) > 0:
                    numero = registro[0].nro_notificacion
                    d = round(dias/(numero+1))

                    aux1 = d
                    for i in range(numero):
                        aux = plan.fecha_fin - datetime.timedelta(days=d)
                        d = d + aux1
                        try:
                            for docente in plan.user_ids:
                                if (docente.has_group('plan_mejoras.res_groups_docente_consejo')):
                                    if aux == today:
                                        template_rec = self.env.ref('plan_mejoras.control_tareas_consejo50')
                                        template_rec.write({'email_to': docente.email})
                                        template_rec.send_mail(plan.id, force_send=True)
                        except:
                            error = True
                        if error == True:
                            self.env.user.notify_danger(
                                message='Se produjo un error al enviar la Notificación al correo electrónico')


    def chek_finalizado(self):
        """
            Método ejecutado con acción planificada 'cron', para notificar mediante correo electrónico a los
            usuarios sobre la finalizacion del Plan Mejoras y cambio del estado del Plan.
        """

        error = False
        today = fields.Date.today()
        lista_plan = self.env["pm.plan"].search([])
        for plan in lista_plan:
            if plan.finalizado == False and plan.fecha_fin < today:
                plan.finalizado = True
                try:
                    for docente in plan.user_ids:
                        if (docente.has_group('plan_mejoras.res_groups_docente_consejo')
                                or docente.has_group('plan_mejoras.res_groups_docente')):
                            template_rec = self.env.ref('plan_mejoras.email_template_plan_finalizado')
                            template_rec.write({'email_to': docente.email})
                            template_rec.send_mail(plan.id, force_send=True)
                except:
                    error = True
                if error == True:
                    self.env.user.notify_danger(
                        message='Se produjo un error al enviar la Notificación al correo electrónico')
            elif plan.finalizado == True and today < plan.fecha_fin:
                plan.finalizado = False


class Debilidad(models.Model):
    _name = "pm.debilidad"
    _description = "Debilidades"

    name = fields.Char(required=True, translate=True, string="Nombre")
    description = fields.Char(string="Descripción")

    tarea_ids = fields.One2many("pm.tarea", "debilidad_id")

    _sql_constraints = [
        ('name_unique', 'unique (name)',
         "El nombre de la Debilidad ya existe!"),
    ]

class NotificacionDias(models.Model):
    _name = "pm.notificaciond"
    _description = "Notificación Días"

    name = fields.Char(translate=True, string="Descripción")
    dias_notificacion = fields.Integer(required=True, translate=True, string="Nro. de días para Notificar la culminacion de las Tareas")

class NotificacionControl(models.Model):
    _name = "pm.notificacionc"
    _description = "Notificación Control"

    name = fields.Char(translate=True, string="Descripción")
    nro_notificacion = fields.Integer(required=True, translate=True, string="Nro. de Notificaciones a ejecutar al Consejo Consultivo")

    @api.model
    def create(self, vals):
        """
            Sobrecarga del método create del NotificacionControl para controlar la creación de un solo registro activo.
            :param vals: Campos del modelo, como una lista de diccionarios.
            :returns: La creación de un nuevo NotificacionControl.
        """

        registros = self.env["pm.notificacionc"].search([])
        if len(registros) > 0:
            raise ValidationError("Ya existe un registro, modifique el actual para el número de "
                                  "Notificaciones al Consejo Consultivo.")

        return super(NotificacionControl, self).create(vals)

    @api.constrains('nro_notificacion')
    def check_numero_notificaion(self):
        """
            Controlar que nro_notificacion no supere de 5, ya que son las veces quye se
            debe notificar al consejo consultivo.
        """

        if self.nro_notificacion > 5:
            raise ValidationError("El número no puede ser mayor a 5")


class confirm_wizard(models.TransientModel):
    _name = 'pm.confirm_wizard'

    yes_no = fields.Char(default='Está seguro que desea comunicar el Plan Mejoras? \n Recuerde que debe socializarlo.')

    def yes(self):
        """
            Redireccionar a la vista Conversaciones en caso se elija la opcion "Ir a comunicar el Plan Mejoras".
            Además de controlar la visibilidad de los botoner Comunicar e Inicializar en la vista Tree del Plan Mejoras.
            :returns: Acción de ventana que redirecciona al módulo de Conversaciones.
        """

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
        """
            Redireccionar a la vista Conversaciones en caso se elija la opcion "Aceptar".
            Además de controlar la visibilidad de los botoner Comunicar e Inicializar en la vista Tree del Plan Mejoras y
            llamar al método para el envío de las notificaciones del inicio del Plan Mejoras.
            :returns: Acción de ventana que redirecciona al módulo de Conversaciones.
        """

        info_id = self.env.context.get('id_ini')
        lista_tareas = self.env["pm.tarea"].search([])
        lista_docentes = self.env["res.users"].search([])
        for tarea in lista_tareas:
            for docente in lista_docentes:
                if int(info_id) == int(tarea.plan_id):
                    if docente.is_group_admin == False and docente.has_group('plan_mejoras.res_groups_docente'):
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
        lista_planes = self.env["pm.plan"].search([])
        lista_docentes = self.env["res.users"].search([])
        for plan in lista_planes:
            if plan.id == info_id:
                for docente in lista_docentes:
                    if docente.has_group('plan_mejoras.res_groups_docente'):
                        docente.write({'plan_id': plan})
                self.env.cr.commit()

        ResUser.action_send_email(self.env.user)
        return {
            "type": "ir.actions.client",
            "tag": "mail.discuss",
            "target": "main"
        }
