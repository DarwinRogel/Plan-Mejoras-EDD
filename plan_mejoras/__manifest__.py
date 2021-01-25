{
    "name": "Plan Mejoras",
    "description":"Modulo de software para el Plan Mejoras de la Evaluacion al Desempeno Docente para la CIS/C",
    "author": "Darwin Rogel - Robin Cordova",

    "summary": """
        Este es un trabajo de titulacion para la obtencion del titulo de Ingeniero en Sistemas
        Permite la optimizacion tecnica del Plan Mejoras de la EDD. en la CIS/C de la Universidad Nacional de Loja
        """,

    "website": "https://unl.edu.ec/",

    "category": "Seguimiento",

    "version": "1.0",
    "depends": ["base"],
    "data": [
        "data/quotation_expiration_cron.xml",
        "security/res_groups.xml",
        "security/ir_rule.xml",
        "security/ir_model_access.xml",
        "report/template.xml",
        "report/report.xml",
        "views/views.xml"
    ]
}