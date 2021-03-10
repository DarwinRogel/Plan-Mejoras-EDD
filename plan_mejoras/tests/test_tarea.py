import unittest
from select import select

from odoo.tests import TransactionCase, tagged, common
from odoo.exceptions import UserError, AccessError, AccessDenied, Warning, ValidationError
class TestModuloPlanMejoras(common.TransactionCase):
    def setUp(self):
        super(TestModuloPlanMejoras, self).setUp()
        self.Users = self.env['res.users'].with_context({'no_reset_password': True})
        self.tarea_obj = self.env['pm.tarea']
        self.estado_obj = self.env['pm.estado']
        self.debilidad_obj = self.env['pm.debilidad']
        self.plan_obj = self.env['pm.plan']
        self.evidencia_obj = self.env['pm.evidencia']

        self.docente = self.Users.create({
            'name': 'Robin Cordova',
            'login': 'robin2',
            'email': 'r.c@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('plan_mejoras.res_groups_docente').id])]})

        self.estado1 = self.estado_obj.create({
            'name': 'Inicio',
            'description': 'Estado del Tablero Kanban Inicio'})

        self.debilidad1 = self.debilidad_obj.create({
            'name': 'Etico',
            'description': 'Debilidad en etica profesional'})

        self.evidencia1 = self.evidencia_obj.create({
            'name': 'Etico',
            'evidencia': 'Debilidad en etica profesional'})

        self.plan1 = self.plan_obj.create({
            'name' : "Plan Mejoras",
            'fecha_inicio' : '2020-10-14 16:00:00',
            'fecha_fin' : '2020-10-14 16:00:00',
            'add_resultados' : True,
            'add_anexos' : True,
            'finalizado' : False,
            'user_ids' : self.docente.id})

        self.tarea1 = self.tarea_obj.create({
            'name': 'Ejecutar un curso de Redes y Telecomunicaciones',
            'fecha_inicio': '2020-10-01 16:00:00',
            'fecha_fin': '2020-10-14 16:00:00',
            'ponderacion': 'nulo',
            'expirado': 'no_expired',
            'estado_id': self.estado1.id,
            'plan_id': self.plan1.id,
            'debilidad_id': self.debilidad1.id,
            'user_id': self.docente.id})

    def test_existe(self):
        self.assertTrue(self.tarea_obj._name in self.env)

    def test_crear_datos_validos(self):
        tarea = self.tarea_obj.create({
            'name': 'Ejecutar un curso de Redes y Telecomunicaciones',
            'fecha_inicio': '2020-10-01 16:00:00',
            'fecha_fin': '2020-10-14 16:00:00',
            'ponderacion': 'nulo',
            'expirado': 'no_expired',
            'estado_id': self.estado1.id,
            'plan_id': self.plan1.id,
            'debilidad_id': self.debilidad1.id,
            'user_id': self.docente.id})
        self.assertTrue(bool(self.tarea_obj.search([('id', '=', tarea.id)], limit=1)))

    def test_eliminar(self):
        tarea = self.tarea_obj.create({
            'name': 'Ejecutar un curso de Redes y Telecomunicaciones',
            'fecha_inicio': '2020-10-01 16:00:00',
            'fecha_fin': '2020-10-14 16:00:00',
            'ponderacion': 'nulo',
            'expirado': 'no_expired'})
        self.assertTrue(tarea, msg=None)
        self.assertTrue(tarea.unlink(), msg=None)

    def test_check_expiry_expired(self):
        tarea = self.tarea_obj.create({
            'name': 'Ejecutar un curso de Redes y Telecomunicaciones',
            'fecha_inicio': '2021-01-15 16:00:00',
            'fecha_fin': '2021-01-14 16:00:00',
            'ponderacion': 'nulo',
            'expirado': 'no_expired',
            'estado_id': self.estado1.id,
            'plan_id': self.plan1.id,
            'debilidad_id': self.debilidad1.id,
            'user_id': self.docente.id})
        tarea.check_expiry()
        self.assertEqual(tarea.expirado, 'expired')

    def test_check_expiry_no_expired(self):
        tarea = self.tarea_obj.create({
            'name': 'Ejecutar un curso de Redes y Telecomunicaciones',
            'fecha_inicio': '2021-01-15 16:00:00',
            'fecha_fin': '2021-03-14 16:00:00',
            'ponderacion': 'nulo',
            'expirado': 'no_expired',
            'estado_id': self.estado1.id,
            'plan_id': self.plan1.id,
            'debilidad_id': self.debilidad1.id,
            'user_id': self.docente.id})
        tarea.check_expiry()
        self.assertEqual(tarea.expirado, 'no_expired')


    #def test_send_notification_tarea(self):
     #   self.tarea1.send_notification_tarea()
      #  self.fail()

    #def test_send_notification_tarea_ponderada(self):
        #self.tarea1.send_notification_tarea()
        #self.fail()







