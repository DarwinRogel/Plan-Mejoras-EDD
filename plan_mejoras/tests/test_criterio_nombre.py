import unittest
from select import select

from odoo.tests import TransactionCase, tagged, common
from odoo.exceptions import UserError, AccessError, AccessDenied, Warning, ValidationError
class TestModuloPlanMejoras(common.TransactionCase):
    def setUp(self):
        super(TestModuloPlanMejoras, self).setUp()

        self.criterio_nombre_obj = self.env['pm.criterionombre']

        self.criterio_nombre1 = self.criterio_nombre_obj.create({
            'name': 'Etico1',
            'porcentaje_ponderacion': 30.0})

    def test_criterio_nombre_existe(self):
        self.assertTrue(self.criterio_nombre_obj._name in self.env)

    def test_criterio_nombre_crear_datos_validos(self):
        criterio_nombre = self.criterio_nombre_obj.create({
            'name': 'Pedagogico1',
            'porcentaje_ponderacion': 30.0})
        self.assertTrue(bool(self.criterio_nombre_obj.search([('id', '=', criterio_nombre.id)], limit=1)))

    @unittest.skip("Es Positivo")
    def test_criterio_nombre_metodo_check_porcentaje_ponderacion_neg(self):
        self.criterio_nombre_obj.create({
            'name': 'Pedagogico1',
            'porcentaje_ponderacion': -1})
        self.fail()

    def test_criterio_nombre_metodo_check_porcentaje_ponderacion_pos(self):
        criterio_nombre = self.criterio_nombre_obj.create({
            'name': 'Pedagogico1',
            'porcentaje_ponderacion': 1})
        self.assertGreater(criterio_nombre.porcentaje_ponderacion, 0,'Es Positivo')

    @unittest.skip("Es Cero")
    def test_criterio_nombre_metodo_check_porcentaje_ponderacion_cero(self):
        self.criterio_nombre_obj.create({
            'name': 'Pedagogico1',
            'porcentaje_ponderacion': 0})
        self.fail()


    def test_criterio_nombre_metodo_compute_valoracion_porcentaje_suma_correcta(self):
        criterio_nombre2 = self.criterio_nombre_obj.create({
            'name': 'Etico2',
            'porcentaje_ponderacion': 30})
        criterio_nombre3 = self.criterio_nombre_obj.create({
            'name': 'Academico1',
            'porcentaje_ponderacion': 30})
        criterio_nombre3._compute_valoracion_porcentaje()
        self.assertEqual(criterio_nombre3.total_val, 100)

    @unittest.skip("Supera 100%")
    def test_criterio_nombre_metodo_compute_valoracion_porcentaje_supera100(self):
        criterio_nombre2 = self.criterio_nombre_obj.create({
            'name': 'Etico2',
            'porcentaje_ponderacion': 40})
        criterio_nombre3 = self.criterio_nombre_obj.create({
            'name': 'Academico',
            'porcentaje_ponderacion': 1})
        criterio_nombre3._compute_valoracion_porcentaje()
        self.fail()



