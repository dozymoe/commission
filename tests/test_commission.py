# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from __future__ import unicode_literals

import unittest
import doctest
from decimal import Decimal

from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import suite as test_suite
from trytond.tests.test_tryton import doctest_teardown
from trytond.tests.test_tryton import doctest_checker
from trytond.pool import Pool

from trytond.modules.company.tests import create_company, set_company


def create_product(name, list_price, cost_price, categories=None):
    pool = Pool()
    Template = pool.get('product.template')
    Product = pool.get('product.product')
    Uom = pool.get('product.uom')

    unit, = Uom.search([('name', '=', 'Unit')])
    template = Template(
        name=name,
        type='service',
        list_price=list_price,
        cost_price=cost_price,
        default_uom=unit,
        products=None,
        )
    if categories:
        template.categories = categories
    template.save()
    product = Product(template=template)
    product.save()
    return product


def create_plan(lines):
    pool = Pool()
    Plan = pool.get('commission.plan')

    commission_product = create_product("Commission", Decimal(10),
        Decimal(3), [])
    plan, = Plan.create([{
                'name': "Commission Plan",
                'commission_product': commission_product.id,
                'lines': [('create', lines)]

                }])
    return plan


class CommissionTestCase(ModuleTestCase):
    'Test Commission module'
    module = 'commission'

    @with_transaction()
    def test_plan_category(self):
        "Test plan with category"
        pool = Pool()
        Category = pool.get('product.category')

        category = Category(name="Category")
        category.save()

        company = create_company()
        with set_company(company):
            product = create_product(
                "Other", Decimal(10), Decimal(3), [category])

            plan = create_plan([{
                        'category': category.id,
                        'formula': 'amount * 0.8',
                        }, {
                        'formula': 'amount',
                        }])

            self.assertEqual(plan.compute(Decimal(1), product), Decimal('0.8'))

            template = product.template
            template.categories = []
            template.save()

            self.assertEqual(plan.compute(Decimal(1), product), Decimal(1))

    @with_transaction()
    def test_plan_no_product(self):
        "Test plan with no product"
        pool = Pool()
        Category = pool.get('product.category')
        PlanLine = pool.get('commission.plan.line')

        category = Category(name="Category")
        category.save()

        company = create_company()
        with set_company(company):
            product = create_product("Other", Decimal(10), Decimal(3))
            plan = create_plan([{
                        'category': category.id,
                        'formula': 'amount * 0.8',
                        }, {
                        'product': product.id,
                        'formula': 'amount * 0.7',
                        }, {
                        'formula': 'amount',
                        }])

            self.assertEqual(plan.compute(Decimal(1), None), Decimal(1))

            PlanLine.delete(plan.lines[1:])

            self.assertEqual(plan.compute(Decimal(1), None), None)


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            CommissionTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_commission.rst',
            tearDown=doctest_teardown, encoding='utf-8',
            checker=doctest_checker,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
