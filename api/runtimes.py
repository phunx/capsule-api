from flask import request
from app import db, oidc
from werkzeug.exceptions import NotFound, BadRequest
from models import Runtime, runtime_schema, runtimes_schema
from models import RoleEnum
from models import AvailableOption, AvailableOptionValidationRule
import json
from utils import oidc_require_role


# GET /runtimes
@oidc.accept_token(require_token=True, render_errors=False)
def search(offset, limit, filters):
    # TODO: test filters with relationships
    #try:
    results = Runtime.query.filter_by(**filters).limit(limit).offset(offset).all()
    #except:
    #    raise BadRequest

    if not results:
        raise NotFound(description="No runtimes have been found.")

    return runtimes_schema.dump(results).data


# POST /runtimes
@oidc_require_role(min_role=RoleEnum.superadmin)
def post():
    runtime_data = request.get_json()
    data = runtime_schema.load(runtime_data).data

    d = dict(data)

    if "available_opts" in d:
        available_opts_array = d["available_opts"]
        available_opts = []
        for opt in available_opts_array:
            if "validation_rules" in opt:
                validation_rules_array = opt["validation_rules"]
                validation_rules = []
                for rule in validation_rules_array:
                    validation_rule = AvailableOptionValidationRule(**rule)
                    validation_rules.append(validation_rule)
                opt.pop("validation_rules")
                available_opt = AvailableOption(**opt, validation_rules=validation_rules)
            else:
                available_opt = AvailableOption(**opt)
            available_opts.append(available_opt)
        d.pop("available_opts")

        runtime = Runtime(**d, available_opts=available_opts)
    else:
        runtime = Runtime(**data)

    db.session.add(runtime)
    db.session.commit()

    result = runtime.query.get(runtime.id)
    return runtime_schema.dump(result).data, 201, {
        'Location': f'{request.base_url}/{runtime.id}',
    }


# GET /runtimes/{rID}
#@oidc.accept_token(require_token=True, render_errors=False)
@oidc_require_role(min_role=RoleEnum.user)
def get(runtime_id):
    try:
        runtime = Runtime.query.get(runtime_id)
    except:
        raise BadRequest

    if runtime is None:
        raise NotFound(description=f"The requested runtime '{runtime_id}' has not been found.")

    return runtime_schema.dump(runtime).data


# PUT /runtimes/{rId}
@oidc_require_role(min_role=RoleEnum.superadmin)
def put(runtime_id, runtime):
    pass


# DELETE /runtimes/{rId}
@oidc_require_role(min_role=RoleEnum.superadmin)
def delete(runtime_id):
    try:
        runtime = Runtime.query.get(runtime_id)
    except:
        raise BadRequest

    if runtime is None:
        raise NotFound(description=f"The requested runtime '{runtime_id}' has not been found.")

    db.session.delete(runtime)
    db.session.commit()
    return None, 204
