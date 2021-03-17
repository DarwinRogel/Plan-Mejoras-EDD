import unittest
from select import select

from odoo.tests import TransactionCase, tagged, common
from odoo.exceptions import UserError, AccessError, AccessDenied, Warning, ValidationError
class TestModuloPlanMejoras(common.TransactionCase):
    def setUp(self):
        super(TestModuloPlanMejoras, self).setUp()
        self.Users = self.env['res.users'].with_context({'no_reset_password': True})
        self.tarea_obj = self.env['pm.tarea']
        self.plan_obj = self.env['pm.plan']
        self.criterio_nombre_obj = self.env['pm.criterionombre']
        self.criterio_obj = self.env['pm.criterio']

        self.docente = self.Users.create({
            'name': 'Raul Perez',
            'login': 'robin1',
            'email': 'r.c@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('plan_mejoras.res_groups_docente').id])]})

        self.docente1 = self.Users.create({
            'name': 'Darwin Rogel',
            'login': 'darwin',
            'email': 'd.r@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [
                (6, 0, [self.env.ref('plan_mejoras.res_groups_docente_consejo').id])]})

        self.docenteF = self.Users.create({
            'name': 'Pedro Daniel',
            'login': 'pedroD',
            'email': 'd.d@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [
                (6, 0, [self.env.ref(
                    'plan_mejoras.res_groups_docente').id])]})

        self.docente2 = self.Users.create({
            'name': 'Juan Montero',
            'login': 'juan',
            'email': 'j.m@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [
                (6, 0, [self.env.ref('plan_mejoras.res_groups_administrador').id])]})

        self.plan1 = self.plan_obj.create({
            'name': "Plan Mejoras",
            'fecha_inicio': '2021-03-01',
            'fecha_fin': '2021-03-28',
            'add_resultados': True,
            'add_anexos': True,
            'finalizado': False,
            'user_ids': [self.docente.id]})

        self.tarea1 = self.tarea_obj.create({
            'name': 'Ejecutar un curso de Redes y Telecomunicaciones',
            'fecha_inicio': '2021-03-01',
            'fecha_fin': '2021-03-18',
            'ponderacion': 'nulo',
            'expirado': 'no_expired',
            'plan_id': self.plan1.id,
            'user_id': self.docente.id})

        self.criterio_nombre1 = self.criterio_nombre_obj.create({
            'name': 'Etico1',
            'porcentaje_ponderacion': 30.0})

        self.criterio_nombre2 = self.criterio_nombre_obj.create({
            'name': 'Academico1',
            'porcentaje_ponderacion': 50.0})

        self.criterio_nombre3 = self.criterio_nombre_obj.create({
            'name': 'Pedagogico1',
            'porcentaje_ponderacion': 20.0})

    def test_crear_datos_validos(self):
        usuario = self.Users.create({
            'name': 'Juan Montalvan',
            'login': 'juan1',
            'email': 'j.m@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [
                (6, 0, [self.env.ref('plan_mejoras.res_groups_docente').id])]})
        self.assertTrue(bool(self.Users.search([('id', '=', usuario.id)], limit=1)))

    def test_grupos_email(self):
        email = ['d.d@example.com', 'robincordova7@gmail.com', 'r.c@example.com']
        email1 = self.Users.get_groups_usesr_email()
        self.assertEqual(email, email1)


    def test_is_admin_true(self):
        self.docente2._compute_is_group_admin()
        self.assertTrue(self.docente2.is_group_admin)

    def test_is_admin_false(self):
        self.docente1._compute_is_group_admin()
        self.assertFalse(self.docente1.is_group_admin)

    def test_contador_tareas_true(self):
        self.docente._contador_tareas()
        self.assertEqual(self.docente.count_tarea, 1)

    def test_contador_tarea_false(self):
        tarea3 = self.tarea_obj.create({
            'name': 'Ejecutar un cursos de Redes',
            'fecha_inicio': '2021-03-01',
            'fecha_fin': '2021-03-18',
            'ponderacion': 'nulo',
            'expirado': 'no_expired',
            'plan_id': self.plan1.id,
            'user_id': self.docenteF.id})

        self.docenteF._contador_tareas()
        self.assertEqual(self.docenteF.count_tarea, 1)

    #def test_valoracion_docente(self):
    #    usuarios = self.Users.create({
    #        'name': 'Pedro Montalvan',
    #        'login': 'pedro',
    #        'email': 'p.r@example.com',
    #        'signature': 'SignBert',
    #        'notification_type': 'email',
    #        'groups_id': [
    #            (6, 0, [self.env.ref('plan_mejoras.res_groups_docente').id])]})
    #
    #   criterio = self.criterio_obj.create({
    #        'calificacion': 30,
    #        'criterionombre_id' : self.criterio_nombre1.id,
    #        'user_id':usuarios.id
    #    })
    #    usuarios._compute_valoracion_docente()
    #    self.assertEqual(usuarios.us_cat, 'insatisfactorio')
