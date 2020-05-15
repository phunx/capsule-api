import pytest
import webtest
from app import create_app
from app import db as _db
from config import TestConfig
from models import *
import tests.foodata as foodata


@pytest.fixture(scope='function')
def app():
    connex_app = create_app(TestConfig)
    return connex_app.app


@pytest.fixture(scope='function')
def testapp(app):
    return webtest.TestApp(app)


@pytest.fixture(scope='function', autouse=True)
def db(app):
    # HACK: app parameter is here to trigger db object configuration
    with app.app_context():
        _db.create_all()

        setup_initial_data(_db)
        yield _db

        _db.session.close()
        _db.drop_all()


def setup_initial_data(db):

    d = dict(foodata.available_opt1)
    d["access_level"] = getattr(RoleEnum, foodata.available_opt1["access_level"])
    d["value_type"] = getattr(OptionValueTypeEnum, foodata.available_opt1["value_type"])
    available_opt1 = AvailableOption(**d)

    d = dict(foodata.validation_rule1)
    d["type"] = getattr(ValidationRuleEnum, foodata.validation_rule1["type"])
    validation_rule1 = AvailableOptionValidationRule(**d)

    d = dict(foodata.validation_rule2)
    d["type"] = getattr(ValidationRuleEnum, foodata.validation_rule2["type"])
    validation_rule2 = AvailableOptionValidationRule(**d)

    d = dict(foodata.available_opt2)
    d["access_level"] = getattr(RoleEnum, foodata.available_opt2["access_level"])
    d["value_type"] = getattr(OptionValueTypeEnum, foodata.available_opt2["value_type"])
    d.pop("validation_rules")
    available_opt2 = AvailableOption(**d,
        validation_rules=[
            validation_rule1,
            validation_rule2]
    )

    d = dict(foodata.runtime1)
    d["runtime_type"] = getattr(RuntimeTypeEnum, foodata.runtime1["runtime_type"])
    d.pop("available_opts")
    runtime1 = Runtime(**d,
        available_opts=[
            available_opt1,
            available_opt2
        ]
    )

    d = dict(foodata.fqdn1)
    fqdn1 = FQDN(**d)

    d = dict(foodata.fqdn2)
    fqdn2 = FQDN(**d)

    d = dict(foodata.option)
    option = Option(**d)

    d = dict(foodata.webapp)
    d.pop("fqdns")
    d.pop("opts")
    webapp1 = WebApp(**d,
        fqdns=[
            fqdn1,
            fqdn2,
        ],
        opts=[
            option,
        ],
        runtime=runtime1,
    )

    users = [User(name=x) for x in foodata.capsule1["owners"]]

    d = dict(foodata.capsule1)
    d.pop("owners")
    capsule1 = Capsule(**d, owners=users)

    array_obj = [
        validation_rule1,
        validation_rule2,
        available_opt1,
        available_opt2,
        runtime1,
        option,
        fqdn1,
        fqdn2,
        webapp1,
        capsule1,
    ]

    for u in users:
        array_obj.append(u)

    db.session.add_all(array_obj)
    db.session.commit()
